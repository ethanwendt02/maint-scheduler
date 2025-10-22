# apps/checklists/management/commands/import_checklist_text.py
import os, re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.checklists.models import ChecklistTemplate, ChecklistItem

# Heuristics to normalize common section names you had in the Notion doc
SECTION_HINTS = {
    r"\bkit\b|\btools?\b|\bsuppl(y|ies)\b": "Maintenance Kit",
    r"\bmaintenance checklist\b|\bchecklist\b": "Checklist",
    r"\b(pre|pre-)?check(s)?\b|\bpre[- ]?inspection\b": "Pre-check",
    r"\bprocedure\b|\bstep[- ]?by[- ]?step\b|\broutine\b": "Procedure",
    r"\babout the robot\b": "About the Robot",
    r"\baccident(s)?\b|\bincident(s)?\b": "Incidents",
    r"\bmaintenance history\b": "Maintenance History",
    r"\bgeneral rules\b|\bguidelines?\b": "General Rules",
    r"\bcleaning\b": "Cleaning",
    r"\binspection\b": "Inspection",
}

def _normalize_section(raw: str) -> str:
    s = raw.strip(" #:*•-").strip()
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # [text](url) → text
    s = re.sub(r"[*_`~>|]", "", s).strip()
    # try hints
    lower = s.lower()
    for pat, name in SECTION_HINTS.items():
        if re.search(pat, lower):
            return name
    # Title-case fallback, but keep short
    return s.title()[:120]

def _clean_line(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)   # strip markdown links
    s = re.sub(r"[🧰⚙️📸🔧✅📗📄📋📎📌💡📍🔍🪛🧽💨🚀🤖⭐️]", "", s)  # emojis
    s = re.sub(r"\[ ?\]", "", s)                    # notion checkboxes
    s = re.sub(r"[*_#>`~]", "", s)                  # md noise
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def _iter_markdown_blocks(text: str):
    """
    Yield tuples of (kind, content) where kind is 'section' for a header
    and 'line' for a potential checklist line.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        # markdown header (##, ### …) → section
        if re.match(r"^#{1,6}\s+\S", line):
            yield ("section", _normalize_section(line.lstrip("#").strip()))
            continue
        # obvious new bullets/numbers are lines
        if re.match(r"^(\d+[.)]|[-*•])\s+\S", line):
            yield ("line", re.sub(r"^(\d+[.)]|[-*•])\s*", "", line))
            continue
        # plain text; still might be section-ish if it’s short + looks like a heading
        if len(line) <= 80 and re.search(r":$|\b(checklist|procedure|kit|rules|inspection)\b", line, re.I):
            yield ("section", _normalize_section(line.rstrip(":")))
        else:
            yield ("line", line)

def _split_grouped(text: str):
    """
    Parse markdown-ish text into [(section, step_text), ...]
    """
    current_section = ""
    steps: list[tuple[str, str]] = []
    buffer = ""

    def flush():
        nonlocal buffer
        if buffer.strip():
            steps.append((current_section, _clean_line(buffer.strip())))
        buffer = ""

    for kind, content in _iter_markdown_blocks(text):
        if kind == "section":
            flush()
            current_section = content
        else:  # line
            # New step if it "looks" like a verb-y sentence start
            if re.match(r"^(Step|Check|Perform|Clean|Inspect|Use|Replace|Verify|Ensure|Run|Document|Record)\b", content, re.I):
                flush()
                buffer = content
            else:
                buffer += (" " if buffer else "") + content
    flush()

    # prune tiny lines
    steps = [(sec, s) for sec, s in steps if len(s) > 4]
    return steps


class Command(BaseCommand):
    help = "Import or update a Checklist Template from Markdown/text, with sections."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to .md or .txt")
        parser.add_argument("--template", required=True, help="Template name to create/update")
        parser.add_argument("--description", default="", help="Optional description")
        parser.add_argument("--preview", type=int, default=0, help="Show first N steps (no DB writes)")

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

        grouped = _split_grouped(text)
        if not grouped:
            raise CommandError("No checklist steps parsed.")

        if preview:
            self.stdout.write(self.style.WARNING(f"Previewing first {preview} parsed steps:"))
            for i, (sec, s) in enumerate(grouped[:preview], 1):
                prefix = f"[{sec}] " if sec else ""
                self.stdout.write(f"[{i}] {prefix}{s}")
            raise CommandError("Preview finished. No DB changes applied.")

        tpl, _ = ChecklistTemplate.objects.get_or_create(name=name, defaults={"description": desc})
        if desc and tpl.description != desc:
            tpl.description = desc
            tpl.save(update_fields=["description"])

        tpl.items.all().delete()
        bulk = [
            ChecklistItem(template=tpl, section=sec[:120], text=txt, order=i + 1)
            for i, (sec, txt) in enumerate(grouped)
        ]
        ChecklistItem.objects.bulk_create(bulk)

        self.stdout.write(self.style.SUCCESS(
            f"Imported '{tpl.name}' with {len(bulk)} items across "
            f"{len({b.section for b in bulk if b.section})} section(s)."
        ))
