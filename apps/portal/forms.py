from django import forms
from .models import ClientTicket, TicketComment

class ClientTicketForm(forms.ModelForm):
    class Meta:
        model = ClientTicket
        fields = ["subject", "description", "priority", "attachment"]

class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "Add a comment…"})
        }
