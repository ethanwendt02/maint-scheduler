# apps/checklists/management/commands/import_checklist_text.py
import os, re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.checklists.models import ChecklistTemplate, ChecklistItem

def _clean_line(s: str) -> str:
    """Remove markdown, HTML, and emoji junk from one line."""
    # Remove HTML tags
    s = re.sub(r"<[^>]+>", "", s)
    # Remove Markdown links [text](url)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    # Remove Markdown formatting (*, _, #, etc.)
    s = re.sub(r"[*_#>`~]", "", s)
    # Remove Notion icons/emojis and bracket boxes
    s = re.sub(r"[🧰⚙️📸🔧✅📗📄📋📎📌💡📍🔍🔧🪛🧽💨🚀🤖⭐️]", "", s)
    s = re.sub(r"\[ ?\]", "", s)
    # Collapse multiple spaces
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def _split_to_steps(text: str) -> list[str]:
    """Split markdown text into clear checklist steps."""
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Break text into raw lines
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    steps: list[str] = []
    buffer = ""

    for line in lines:
        # A new step starts if line looks like a bullet, number, or header
        if re.match(r"^(\d+[.)]|[-*•#])\s*", line):
            if buffer:
                steps.append(buffer.strip())
            buffer = re.sub(r"^(\d+[.)]|[-*•#])\s*", "", line)
        # Also split when we hit keywords like "Step", "Maintenance", "Checklist", etc.
        elif re.match(r"^(Step|Check|Perform|Clean|Inspect|Use|Replace|Verify|Ensure)\b", line, re.I):
            if buffer:
                steps.append(buffer.strip())
            buffer = line
        else:
            # continuation of previous step
            buffer += " " + line

    if buffer:
        steps.append(buffer.strip())

    # Clean & filter
    cleaned = [_clean_line(s) for s in steps]
    cleaned = [s for s in cleaned if len(s) > 4]
    return cleaned

class Command(BaseCommand):
    help = "Import or update a Checklist Template from Markdown or text."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to .md or .txt")
        parser.add_argument("--template", required=True, help="Template name to create/update")
        parser.add_argument("--description", default="", help="Optional description")
        parser.add_argument("--preview", type=int, default=0, help="Show first N steps")

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

        steps = _split_to_steps(text)
        if not steps:
            raise CommandError("No checklist steps parsed.")

        if preview:
            self.stdout.write(self.style.WARNING(f"Previewing first {preview} parsed steps:"))
            for i, s in enumerate(steps[:preview], 1):
                self.stdout.write(f"[{i}] {s}")
            raise CommandError("Preview finished. No DB changes applied.")

        tpl, _ = ChecklistTemplate.objects.get_or_create(name=name, defaults={"description": desc})
        if desc and tpl.description != desc:
            tpl.description = desc
            tpl.save(update_fields=["description"])

        tpl.items.all().delete()
        bulk = [ChecklistItem(template=tpl, order=i + 1, text=txt) for i, txt in enumerate(steps)]
        ChecklistItem.objects.bulk_create(bulk)

        self.stdout.write(self.style.SUCCESS(f"Imported '{tpl.name}' with {len(bulk)} steps."))
