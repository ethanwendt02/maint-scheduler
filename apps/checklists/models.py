# apps/checklists/models.py
from django.conf import settings
from django.db import models


class ChecklistRun(models.Model):
    completed_pdf = models.FileField(
        upload_to="completed_checklists/",
        null=True,
        blank=True,
        help_text="Upload the completed checklist PDF"
    )
    template = models.ForeignKey(
        "checklists.ChecklistTemplate",
        null=True, blank=True,
        on_delete=models.PROTECT,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        related_name="created_checklist_runs",
        on_delete=models.SET_NULL,
    )
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        related_name="signed_checklist_runs",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ("-started_at",)

    def __str__(self):
        # handles null template safely
        name = self.template.name if self.template else "Checklist"
        return f"Run of {name} @ {self.started_at:%Y-%m-%d %H:%M}"


class ChecklistTemplate(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)   # ✅ timestamps
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class ChecklistItem(models.Model):
    template = models.ForeignKey(
        ChecklistTemplate,
        related_name="items",
        on_delete=models.CASCADE,
    )
    section = models.CharField(max_length=120, blank=True, db_index=True, default="")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("template_id", "section", "order", "id")

    def __str__(self) -> str:
        sec = f"[{self.section}] " if self.section else ""
        return f"{sec}{self.text[:70]}"
