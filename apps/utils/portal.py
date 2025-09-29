# apps/utils/portal.py
from typing import Optional
from django.contrib.auth import get_user_model
from apps.fleet.models import ClientGroup, Site
from apps.policies.models import MaintenancePolicy
from apps.workorders.models import WorkOrder

User = get_user_model()


def get_portal_site_for(user: User) -> Optional[Site]:
    """
    Resolve the client's Site. Strategy:
    1) First ClientGroup the user belongs to (user.client_groups) -> its Site
    2) Otherwise: None
    """
    cg = (getattr(user, "client_groups", None) or ClientGroup.objects.none()) \
            .select_related("site").first()
    return cg.site if cg else None


def portal_policies_for(user: User):
    """
    Published policies for the user's site.
    Returns an empty queryset if no site can be resolved.
    """
    site = get_portal_site_for(user)
    if not site:
        return MaintenancePolicy.objects.none()
    return (MaintenancePolicy.objects
            .filter(site=site, published=True)
            .order_by("priority", "name", "id"))


def portal_tickets_for(user: User):
    """
    Tickets (work orders) for the user's site, newest first.
    Returns an empty queryset if no site can be resolved.
    """
    site = get_portal_site_for(user)
    if not site:
        return WorkOrder.objects.none()
    return (WorkOrder.objects
            .filter(site=site)
            .order_by("-due_by", "-created_at", "-id"))
