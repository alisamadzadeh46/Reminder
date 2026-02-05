from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from sms.models import OutboundSMS, SMSStatus, SMSTemplate
from .utils import queue_sms, render_template_body


def _can_manage_sms(user):
    return user.is_superuser or user.is_staff


class SMSFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "جستجو در شماره/متن/خطا..."}
    ))
    status = forms.ChoiceField(
        required=False,
        choices=[("", "همه وضعیت‌ها")] + list(SMSStatus.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )


class SMSSendForm(forms.Form):
    to = forms.CharField(
        label="شماره موبایل",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: 09xxxxxxxxx"})
    )
    template_key = forms.ModelChoiceField(
        label="قالب (اختیاری)",
        required=False,
        queryset=SMSTemplate.objects.filter(is_active=True).order_by("key"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    message = forms.CharField(
        label="متن پیام",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "متن پیام... اگر قالب انتخاب کردی می‌تونی خالی بذاری"})
    )

    def clean(self):
        cleaned = super().clean()
        tpl = cleaned.get("template_key")
        msg = (cleaned.get("message") or "").strip()
        if not tpl and not msg:
            raise forms.ValidationError("یا قالب انتخاب کنید یا متن پیام را وارد کنید.")
        return cleaned


@login_required
@user_passes_test(_can_manage_sms)
def sms_outbox(request):
    qs = OutboundSMS.objects.select_related("template", "user").order_by("-created_at")

    form = SMSFilterForm(request.GET or None)
    if form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        status = form.cleaned_data.get("status") or ""

        if q:
            qs = qs.filter(
                Q(to__icontains=q) |
                Q(body__icontains=q) |
                Q(error__icontains=q) |
                Q(provider_message_id__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "sms/outbox.html", {
        "filter_form": form,
        "page_obj": page_obj,
    })


@login_required
@user_passes_test(_can_manage_sms)
def sms_detail(request, pk: int):
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
                msg = render_template_body(tpl, context={})

            queue_sms(to=to, body=msg, user=request.user, template=tpl, idempotency_key="")
            messages.success(request, "پیامک در صف ارسال قرار گرفت.")
            return redirect("sms-outbox")
        messages.error(request, "لطفاً خطاهای فرم را اصلاح کنید.")
    else:
        form = SMSSendForm()

    return render(request, "sms/send.html", {"form": form})