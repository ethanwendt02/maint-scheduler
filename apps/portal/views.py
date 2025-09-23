# apps/portal/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.shortcuts import redirect
from django.contrib import messages

from .models import ClientTicket, TicketComment
from .forms import ClientTicketForm, TicketCommentForm


def _org_for(request):
    cp = getattr(request.user, "clientprofile", None)
    return cp.organization if cp else None


def _portal_ticket_qs(request):
    qs = ClientTicket.objects.select_related("created_by", "organization")
    org = _org_for(request)
    return qs.filter(organization=org) if org else qs.none()


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portal/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["org"] = _org_for(self.request)
        # show the same tickets as the list view (most recent first)
        ctx["recent_tickets"] = _portal_ticket_qs(self.request).order_by("-created_at")[:5]
        return ctx


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(self.request.get_full_path())


class TicketListView(LoginRequiredMixin, ListView):
    model = ClientTicket
    template_name = "portal/ticket_list.html"
    context_object_name = "object_list"  # keep if your template expects object_list

    def get_queryset(self):
        return _portal_ticket_qs(self.request).order_by("-created_at")


class AdminTicketListView(StaffRequiredMixin, ListView):
    model = ClientTicket
    template_name = "portal/admin_ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 25

    def get_queryset(self):
        qs = ClientTicket.objects.select_related("created_by", "organization")
        status = self.request.GET.get("status")
        return qs.filter(status=status) if status else qs


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = ClientTicket
    form_class = ClientTicketForm
    template_name = "portal/ticket_form.html"
    success_url = reverse_lazy("portal:tickets")

    def form_valid(self, form):
        user = self.request.user
        form.instance.created_by = user

        client_profile = getattr(user, "clientprofile", None)
        if not client_profile or not getattr(client_profile, "organization", None):
            messages.error(self.request, "Your account isn’t linked to an organization yet. Please contact support.")
            return redirect(self.success_url)

        form.instance.organization = client_profile.organization
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below and try again.")
        return super().form_invalid(form)


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = ClientTicket
    template_name = "portal/ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        org = _org_for(self.request)
        if org:
            return ClientTicket.objects.filter(organization=org)
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ClientTicket.objects.all()
        return ClientTicket.objects.none()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            TicketComment.objects.create(
                ticket=self.object, author=request.user, body=form.cleaned_data["body"]
            )
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Please write a comment.")
        return redirect("portal:ticket_detail", pk=self.object.pk)


class AdminTicketDetailView(StaffRequiredMixin, DetailView):
    model = ClientTicket
    template_name = "portal/admin_ticket_detail.html"
    context_object_name = "ticket"


class PolicyView(LoginRequiredMixin, TemplateView):
    template_name = "portal/policy.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = _org_for(self.request)
        ctx["org"] = org
        try:
            from apps.policies.models import Policy  # adjust if your model is named differently
            ctx["policy"] = Policy.objects.filter(organization=org).order_by("-id").first() if org else None
        except Exception:
            ctx["policy"] = None
        return ctx




