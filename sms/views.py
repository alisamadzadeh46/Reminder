from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import OutboundSMS, SMSTemplate, SMSStatus
from .utils import queue_sms, render_template_body

def _can_manage_sms(user):
    return user.is_superuser or user.is_staff

class SMSFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"class":"form-control","placeholder":"جستجو..."}))
    status = forms.ChoiceField(required=False, choices=[("", "همه وضعیت‌ها")] + list(SMSStatus.choices), widget=forms.Select(attrs={"class":"form-select"}))

class SMSSendForm(forms.Form):
    to = forms.CharField(label="شماره", widget=forms.TextInput(attrs={"class":"form-control"}))
    template_key = forms.ModelChoiceField(label="قالب (اختیاری)", required=False, queryset=SMSTemplate.objects.filter(is_active=True), widget=forms.Select(attrs={"class":"form-select"}))
    message = forms.CharField(label="متن", required=False, widget=forms.Textarea(attrs={"class":"form-control","rows":4}))
    def clean(self):
        c = super().clean()
        if not c.get("template_key") and not (c.get("message") or "").strip():
            raise forms.ValidationError("یا قالب انتخاب کنید یا متن وارد کنید.")
        return c

@login_required
@user_passes_test(_can_manage_sms)
def sms_outbox(request):
    qs = OutboundSMS.objects.select_related("template","user").order_by("-created_at")
    form = SMSFilterForm(request.GET or None)
    if form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        status = form.cleaned_data.get("status") or ""
        if q:
            qs = qs.filter(Q(to__icontains=q)|Q(body__icontains=q)|Q(error__icontains=q))
        if status:
            qs = qs.filter(status=status)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page",1))
    return render(request, "sms/outbox.html", {"filter_form":form,"page_obj":page_obj})

@login_required
@user_passes_test(_can_manage_sms)
def sms_detail(request, pk):
    sms = get_object_or_404(OutboundSMS.objects.select_related("template","user"), pk=pk)
    return render(request, "sms/detail.html", {"sms":sms})

@login_required
@user_passes_test(_can_manage_sms)
def sms_send(request):
    if request.method=="POST":
        form = SMSSendForm(request.POST)
        if form.is_valid():
            to = form.cleaned_data["to"].strip()
            tpl = form.cleaned_data.get("template_key")
            msg = (form.cleaned_data.get("message") or "").strip()
            if tpl and not msg:
                msg = render_template_body(tpl,{})
            queue_sms(to=to, body=msg, user=request.user, template=tpl)
            messages.success(request, "پیامک در صف قرار گرفت.")
            return redirect("sms-outbox")
        messages.error(request, "فرم معتبر نیست.")
    else:
        form = SMSSendForm()
    return render(request, "sms/send.html", {"form":form})