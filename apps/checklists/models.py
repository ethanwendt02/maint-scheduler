# apps/checklists/models.py
from django.db import models

class ChecklistTemplate(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class ChecklistItem(models.Model):
    template = models.ForeignKey(
        ChecklistTemplate, related_name="items", on_delete=models.CASCADE
    )
    # NEW: optional grouping header for this item
    section = models.CharField(max_length=120, blank=True, db_index=True, default="")
    # existing text of the step
    text = models.TextField()
    # order within its template
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("template_id", "section", "order", "id")

    def __str__(self) -> str:
        sec = f"[{self.section}] " if self.section else ""
        return f"{sec}{self.text[:70]}"
