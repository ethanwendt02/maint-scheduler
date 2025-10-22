# apps/checklists/management/commands/import_checklist_text.py
import os, re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.checklists.models import ChecklistTemplate, ChecklistItem

def _lines_from_text(s: str) -> list[str]:
    # normalize bullets and break into steps
    s = s.replace("\r\n", "\n")
    s = s.replace("\r", "\n")
    # common bullets from Notion/Markdown
    s = re.sub(r"^[ \t]*[-*•]\s+", "", s, flags=re.MULTILINE)
    # collapse double spaces
    s = re.sub(r"[ \t]+", " ", s)
    # split on blank line or newline before capital/bullet-ish
    raw = [ln.strip(" \t-•") for ln in s.split("\n") if ln.strip()]
    # merge lines that are obviously wrapped sentences
    out = []
    buf = ""
    for ln in raw:
        if not buf:
            buf = ln
        else:
            # if previous doesn’t end a sentence, join
            if not re.search(r"[.!?:]\s*$", buf) and (len(ln) < 120):
                buf += " " + ln
            else:
                out.append(buf.strip())
                buf = ln
    if buf:
        out.append(buf.strip())
    # drop super short crumbs
    out = [x for x in out if len(x) > 3]
    return out

class Command(BaseCommand):
    help = "Import/Upsert a Checklist Template from a plain text or Markdown file."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to .txt/.md")
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
            raise CommandError("No steps parsed from file.")

        if preview:
            self.stdout.write(self.style.WARNING("Previewing first %d parsed steps:" % preview))
            for i, s in enumerate(steps[:preview], 1):
                self.stdout.write(f"[{i}] {s}")
            raise CommandError("Preview finished. No DB changes applied.")

        tpl, _ = ChecklistTemplate.objects.get_or_create(name=name, defaults={"description": desc})
        if desc and tpl.description != desc:
            tpl.description = desc
            tpl.save(update_fields=["description"])

        # Upsert items by position
        # Simple strategy: replace existing items with new ordered list
        tpl.items.all().delete()
        bulk = [ChecklistItem(template=tpl, order=i+1, text=txt) for i, txt in enumerate(steps)]
        ChecklistItem.objects.bulk_create(bulk)

        self.stdout.write(self.style.SUCCESS(f"Imported template '{tpl.name}' with {len(bulk)} steps."))
