from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.workorders.models import WorkOrder
from apps.checklists.models import ChecklistRun

class Command(BaseCommand):
    help = "Create default roles/groups with permissions"

    def handle(self, *args, **kwargs):
        roles = {
            "Technician": {
                # can view work orders and create checklist runs
                "perms": [
                    "view_workorder",
                    "view_checklistrun", "add_checklistrun", "change_checklistrun",
                ],
            },
            "Planner": {
                # can create/assign work orders
                "perms": [
                    "view_workorder", "add_workorder", "change_workorder",
                    "view_checklistrun",
                ],
            },
            "Supervisor": {
                # full control on work orders and checklist runs
                "perms": [
                    "view_workorder", "add_workorder", "change_workorder", "delete_workorder",
                    "view_checklistrun", "add_checklistrun", "change_checklistrun", "delete_checklistrun",
                ],
            },
            "Client": {
                # read-only
                "perms": ["view_workorder", "view_checklistrun"],
            },
        }

        # collect permissions
        ct_wo  = ContentType.objects.get_for_model(WorkOrder)
        ct_run = ContentType.objects.get_for_model(ChecklistRun)

        perm_map = {
            "workorder": {p.codename: p for p in Permission.objects.filter(content_type=ct_wo)},
            "checklistrun": {p.codename: p for p in Permission.objects.filter(content_type=ct_run)},
        }

        for role, cfg in roles.items():
            g, _ = Group.objects.get_or_create(name=role)
            g.permissions.clear()
            for codename in cfg["perms"]:
                # figure out which model it belongs to by suffix
                if codename.endswith("workorder"):
                    p = perm_map["workorder"].get(codename)
                else:
                    p = perm_map["checklistrun"].get(codename)
                if p:
                    g.permissions.add(p)
            self.stdout.write(self.style.SUCCESS(f"Role synced: {role}"))
