from django import forms
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    class Meta:
        model = Document
        fields = ["document_file"]
        widgets = {
            "document_file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.docx,.txt",
                }
            )
        }

    def clean_document_file(self):
        file = self.cleaned_data["document_file"]

        if not file.name.lower().endswith(self.ALLOWED_EXTENSIONS):
            raise forms.ValidationError(
                "Only PDF, DOCX and TXT files are allowed."
            )

        if file.size == 0:
            raise forms.ValidationError(
                "The uploaded file is empty."
            )

        if file.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError(
                f"File size must not exceed {self.MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        return file