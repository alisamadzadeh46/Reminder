from django import forms
from .models import Meeting, Invitation

class MeetingCreateForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["title", "description", "start_at", "end_at", "location", "secretary", "follow_up_owner", "approver"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "start_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "secretary": forms.Select(attrs={"class": "form-select"}),
            "follow_up_owner": forms.Select(attrs={"class": "form-select"}),
            "approver": forms.Select(attrs={"class": "form-select"}),
        }


class InviteeAddForm(forms.Form):
    # ساده‌ترین حالت: وارد کردن username یا email
    invitee_identifier = forms.CharField(
        label="نام کاربری یا ایمیل مدعو",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
