from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from datetime import timedelta
from .models import SMSTemplate
from .utils import queue_sms, render_template_body
from django.utils.timezone import now
from .models import OutboundSMS, SMSStatus


def _can_manage_sms(user):
    return user.is_superuser or user.is_staff


class SMSFilterForm(forms.Form):
    q = forms.CharField(required=False,
                        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "جستجو..."}))
    status = forms.ChoiceField(required=False, choices=[("", "همه وضعیت‌ها")] + list(SMSStatus.choices),
                               widget=forms.Select(attrs={"class": "form-select"}))


class SMSSendForm(forms.Form):
    to = forms.CharField(label="شماره", widget=forms.TextInput(attrs={"class": "form-control"}))
    template_key = forms.ModelChoiceField(label="قالب (اختیاری)", required=False,
                                          queryset=SMSTemplate.objects.filter(is_active=True),
                                          widget=forms.Select(attrs={"class": "form-select"}))
    message = forms.CharField(label="متن", required=False,
                              widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}))

    def clean(self):
        c = super().clean()
        if not c.get("template_key") and not (c.get("message") or "").strip():
            raise forms.ValidationError("یا قالب انتخاب کنید یا متن وارد کنید.")
        return c


@login_required
@user_passes_test(_can_manage_sms)
def sms_outbox(request):
    qs = OutboundSMS.objects.select_related("template", "user").order_by("-created_at")
    form = SMSFilterForm(request.GET or None)
    if form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        status = form.cleaned_data.get("status") or ""
        if q:
            qs = qs.filter(Q(to__icontains=q) | Q(body__icontains=q) | Q(error__icontains=q))
        if status:
            qs = qs.filter(status=status)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "sms/outbox.html", {"filter_form": form, "page_obj": page_obj})


@login_required
@user_passes_test(_can_manage_sms)
def sms_detail(request, pk):
    sms = get_object_or_404(OutboundSMS.objects.select_related("template", "user"), pk=pk)
    return render(request, "sms/detail.html", {"sms": sms})


@login_required
@user_passes_test(_can_manage_sms)
def sms_send(request):
    if request.method == "POST":
        form = SMSSendForm(request.POST)
        if form.is_valid():
            to = form.cleaned_data["to"].strip()
            tpl = form.cleaned_data.get("template_key")
            msg = (form.cleaned_data.get("message") or "").strip()
            if tpl and not msg:
                msg = render_template_body(tpl, {})
            queue_sms(to=to, body=msg, user=request.user, template=tpl)
            messages.success(request, "پیامک در صف قرار گرفت.")
            return redirect("sms-outbox")
        messages.error(request, "فرم معتبر نیست.")
    else:
        form = SMSSendForm()
    return render(request, "sms/send.html", {"form": form})


@csrf_exempt
def delivery_report(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid method"}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "invalid json"}, status=400)

    provider_id = data.get("BatchSmsId")
    status = data.get("Status")

    if not provider_id:
        return JsonResponse({"error": "missing id"}, status=400)

    from .models import OutboundSMS, SMSStatus

    try:
        with transaction.atomic():
            sms = OutboundSMS.objects.select_for_update().get(
                provider_message_id=str(provider_id)
            )

            if status == "DELIVERED":
                sms.mark_delivered(provider_response=json.dumps(data))
            elif status == "FAILED":
                sms.mark_failed(
                    error="Delivery failed",
                    provider_response=json.dumps(data)
                )

    except OutboundSMS.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse({"ok": True})


@login_required
def user_dashboard(request):
    qs = OutboundSMS.objects.filter(user=request.user).order_by("-created_at")

    total = qs.count()
    sent = qs.filter(status=SMSStatus.SENT).count()
    failed = qs.filter(status=SMSStatus.FAILED).count()
    success_rate = int((sent / total) * 100) if total else 0

    # 📊 چارت ۷ روز اخیر
    labels = []
    data = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        labels.append(day.strftime("%m/%d"))
        data.append(qs.filter(created_at__date=day).count())

    # 📄 Pagination
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "total": total,
        "sent": sent,
        "failed": failed,
        "success_rate": success_rate,
        "chart_labels": json.dumps(labels),
        "chart_data": json.dumps(data),
        "page_obj": page_obj,
    }

    return render(request, "sms/user_dashboard.html", context)


def is_admin(user):
    return user.is_staff


@user_passes_test(is_admin)
def admin_dashboard(request):
    qs = OutboundSMS.objects.all()

    total = qs.count()
    sent = qs.filter(status=SMSStatus.SENT).count()
    failed = qs.filter(status=SMSStatus.FAILED).count()
    success_rate = int((sent / total) * 100) if total else 0

    labels = []
    data = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        labels.append(day.strftime("%m/%d"))
        data.append(qs.filter(created_at__date=day).count())

    # 📄 Pagination
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "total": total,
        "sent": sent,
        "failed": failed,
        "success_rate": success_rate,
        "chart_labels": json.dumps(labels),
        "chart_data": json.dumps(data),
        "page_obj": page_obj,
    }

    return render(request, "sms/admin_dashboard.html", context)
