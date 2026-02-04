from django import forms
from .models import Task

class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["meeting", "title", "description", "assignee", "due_date", "follower", "approver"]
        widgets = {
            "meeting": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "follower": forms.Select(attrs={"class": "form-select"}),
            "approver": forms.Select(attrs={"class": "form-select"}),
        }
