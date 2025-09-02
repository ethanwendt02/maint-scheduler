# apps/portal/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import ClientTicket, TicketComment
from .forms import ClientTicketForm, TicketCommentForm

def _org_for(request):
    # Helper: returns user's org if they have a clientprofile
    cp = getattr(request.user, "clientprofile", None)
    return cp.organization if cp else None


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portal/dashboard.html"


class TicketListView(LoginRequiredMixin, ListView):
    model = ClientTicket
    template_name = "portal/ticket_list.html"
    context_object_name = "object_list"

    
    def get_queryset(self):
        qs = super().get_queryset().select_related("created_by", "organization")
        org = _org_for(self.request)
        if org:
            qs = qs.filter(organization=org)
        else:
            qs = qs.none()
        return qs


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = ClientTicket
    form_class = ClientTicketForm
    template_name = "portal/ticket_form.html"
    success_url = reverse_lazy("portal:tickets")

    def form_valid(self, form):
        org = _org_for(self.request)
        form.instance.organization = org
        form.instance.created_by = self.request.user
        messages.success(self.request, "Ticket created.")
        return super().form_valid(form)


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = ClientTicket
    template_name = "portal/ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        # scope to the current user's org
        org = getattr(self.request.user, "clientprofile", None)
        if org:
            return ClientTicket.objects.filter(organization=org.organization)
        # fallback: if staff/admin, allow all
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ClientTicket.objects.all()
        return ClientTicket.objects.none()

    def post(self, request, *args, **kwargs):
        # Handle comment submission
        self.object = self.get_object()
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            TicketComment.objects.create(
                ticket=self.object,
                author=request.user,
                body=form.cleaned_data["body"],
            )
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Please write a comment.")
        return redirect("portal:ticket_detail", pk=self.object.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comment_form"] = TicketCommentForm()
        return ctx


class PolicyView(LoginRequiredMixin, TemplateView):
    template_name = "portal/policy.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request.user, "clientprofile", None)
        org = org.organization if org else None
        ctx["org"] = org

        # OPTIONAL: pull a policy record if your policies app has one
        # Adjust model/fields to match your real schema.
        try:
            from apps.policies.models import Policy  # or whatever your model is
            policy = None
            if org:
                policy = Policy.objects.filter(organization=org).order_by("-id").first()
            ctx["policy"] = policy
        except Exception:
            ctx["policy"] = None

        return ctx



