# apps/checklists/management/commands/import_checklist_text.py
import os, re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.checklists.models import ChecklistTemplate, ChecklistItem

def _clean_markdown(s: str) -> str:
    """
    Strip Markdown/HTML/Notion formatting from a line of text.
    """
    # Remove HTML tags
    s = re.sub(r"<[^>]+>", "", s)
    # Remove Markdown links [text](url)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    # Remove bold/italic/code markers
    s = re.sub(r"[*_`#>~]", "", s)
    # Replace multiple spaces
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def _lines_from_text(s: str) -> list[str]:
    """
    Normalize bullets and split into logical steps.
    """
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"^[ \t]*[-*•]\s+", "", s, flags=re.MULTILINE)
    s = re.sub(r"[ \t]+", " ", s)

    raw_lines = [ln.strip(" \t-•") for ln in s.split("\n") if ln.strip()]
    merged: list[str] = []
    buf = ""
    for ln in raw_lines:
        if not buf:
            buf = ln
        else:
            # Start a new step if the line looks like a heading, bullet, or capital start
            if re.match(r"^(#|##|###|\d+[.)]|[-*•])", ln):
                merged.append(buf.strip())
                buf = ln
            else:
                buf += " " + ln
    if buf:
        merged.append(buf.strip())

    # Clean and filter
    cleaned = [_clean_markdown(x) for x in merged]
    cleaned = [x for x in cleaned if len(x) > 3]
    return cleaned

class Command(BaseCommand):
    help = "Import/Upsert a Checklist Template from a Markdown or text file."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to .md or .txt file")
        parser.add_argument("--template", required=True, help="Template name to create/update")
        parser.add_argument("--description", default="", help="Optional description")
        parser.add_argument("--preview", type=int, default=0, help="Show first N steps without writing")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["path"]
        name = opts["template"]
        desc = opts["description"]
        preview = int(opts["preview"] or 0)

        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        steps = _lines_from_text(text)
        if not steps:
            raise CommandError("No checklist steps parsed — verify Markdown export.")

        if preview:
            self.stdout.write(self.style.WARNING(f"Previewing first {preview} parsed steps:"))
            for i, s in enumerate(steps[:preview], 1):
                self.stdout.write(f"[{i}] {s}")
            raise CommandError("Preview finished. No DB changes applied.")

        tpl, _ = ChecklistTemplate.objects.get_or_create(name=name, defaults={"description": desc})
        if desc and tpl.description != desc:
            tpl.description = desc
            tpl.save(update_fields=["description"])

        # Replace existing items
        tpl.items.all().delete()
        bulk = [ChecklistItem(template=tpl, order=i + 1, text=txt) for i, txt in enumerate(steps)]
        ChecklistItem.objects.bulk_create(bulk)

        self.stdout.write(self.style.SUCCESS(f"Imported template '{tpl.name}' with {len(bulk)} steps."))
