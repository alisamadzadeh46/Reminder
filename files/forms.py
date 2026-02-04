from django import forms
from .models import Attachment

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["title", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "عنوان فایل (اختیاری)"}),
        }
