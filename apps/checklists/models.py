# apps/checklists/models.py
from django.db import models
from django.conf import settings

# If you already have this, keep yours and remove this stub
class ChecklistTemplate(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    def __str__(self): return self.name

class ChecklistItem(models.Model):
    template = models.ForeignKey(ChecklistTemplate, related_name="items", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    text = models.CharField(max_length=255)
    required = models.BooleanField(default=True)
    # Optional: “kit items” per step (free text or JSON)
    kit_items = models.TextField(blank=True, default="", help_text="Comma-separated parts/tools")
    class Meta:
        ordering = ("order", "id")
    def __str__(self): return f"[{self.order}] {self.text}"

class ChecklistRun(models.Model):
    template = models.ForeignKey(ChecklistTemplate, related_name="runs", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    # optional generic link to what this run is for
    # we'll also link it directly from WorkOrder (below)
    def __str__(self): return f"Run of {self.template.name} @ {self.created_at:%Y-%m-%d}"

    @property
    def progress(self):
        total = self.items.count()
        if not total: return "0/0"
        done = self.items.filter(done=True).count()
        return f"{done}/{total}"

class ChecklistRunItem(models.Model):
    run = models.ForeignKey(ChecklistRun, related_name="items", on_delete=models.CASCADE)
    template_item = models.ForeignKey(ChecklistItem, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)
    text = models.CharField(max_length=255)
    kit_items = models.TextField(blank=True, default="")
    done = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        prefix = "✓" if self.done else "□"
        return f"{prefix} {self.text}"

