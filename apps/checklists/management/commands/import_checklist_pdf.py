import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.checklists.models import ChecklistTemplate, ChecklistItem
from PyPDF2 import PdfReader


class Command(BaseCommand):
    help = "Import checklist steps from a maintenance PDF (e.g., exported from Notion)."

    def add_arguments(self, parser):
        parser.add_argument("pdf_path", help="Path to the PDF file")
        parser.add_argument("--template", required=True, help="Template name to create/update")
        parser.add_argument("--description", default="", help="Template description (optional)")
        parser.add_argument("--append", action="store_true", help="Append to existing items instead of replacing them")
        parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB writes")
        parser.add_argument("--preview", type=int, default=0, help="Show first N parsed steps and exit")

    @transaction.atomic
    def handle(self, *args, **opts):
        pdf_path = opts["pdf_path"]
        if not os.path.exists(pdf_path):
            raise CommandError(f"PDF not found: {pdf_path}")

        template_name = opts["template"].strip()
        description = opts["description"].strip()
        append = bool(opts.get("append"))
        dry = bool(opts.get("dry_run"))
        preview = int(opts.get("preview") or 0)

        # Extract text from PDF
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # Split into lines
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        steps = []

        # Basic heuristic to identify steps or items
        for ln in lines:
            if re.match(r"^\d+[\).]", ln):  # numbered list (e.g., 1., 2), etc.)
                steps.append(ln)
            elif any(keyword in ln.lower() for keyword in ["inspect", "clean", "check", "remove", "replace", "verify", "reinstall", "run", "use"]):
                steps.append(ln)
            elif "kit" in ln.lower() or "tool" in ln.lower():
                steps.append(f"[KIT] {ln}")

        if not steps:
            raise CommandError("No checklist steps were found in this PDF — make sure it’s text-based, not scanned.")

        if preview:
            self.stdout.write(self.style.WARNING(f"Previewing first {preview} parsed steps:"))
            for i, s in enumerate(steps[:preview], 1):
                self.stdout.write(f"[{i}] {s}")
            raise CommandError("Preview finished. No DB changes applied.")

        # Upsert template
        template, created = ChecklistTemplate.objects.get_or_create(
            name=template_name,
            defaults={"description": description} if "description" in [f.name for f in ChecklistTemplate._meta.get_fields()] else {},
        )

        if not append:
            if not dry:
                template.items.all().delete()

        # Build and insert items
        created_items = 0
        for order, step in enumerate(steps, start=1):
            required = not step.startswith("[KIT]")
            text = step.replace("[KIT]", "").strip()
            kit_items = text if not required else ""

            if not dry:
                ChecklistItem.objects.create(
                    template=template,
                    order=order,
                    text=text,
                    required=required,
                    kit_items=kit_items if not required else "",
                )
            created_items += 1

        self.stdout.write(self.style.SUCCESS(
            f"ChecklistTemplate {'created' if created else 'updated'}: {template.name!r}. "
            f"items_imported={created_items}, dry_run={dry}"
        ))
