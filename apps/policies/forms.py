from django import forms
from .models import MaintenanceRecord

class MaintenanceRecordUploadForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ["file", "notes"]

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Please upload a PDF file.")
        if f.size > 15 * 1024 * 1024:
            raise forms.ValidationError("PDF must be under 15MB.")
        return f
