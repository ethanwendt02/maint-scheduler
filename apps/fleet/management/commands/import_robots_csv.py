# apps/fleet/management/commands/import_robots_csv.py
import csv
import re
import os
import typing as t

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.fleet.models import Robot, Site, Payload, Contact


def _split_multi(val: str, seps: str = ",;") -> t.List[str]:
    if not val:
        return []
    out: t.List[str] = []
    buf = ""
    for ch in val:
        if ch in seps:
            if buf.strip():
                out.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


def _extract_labeled(text: str, label: str) -> str:
    """
    From a blob like 'Serial: spot-BD-123, Wi-Fi Password: ...',
    extract the value for the given label.
    """
    if not text:
        return ""
    import re
    pat = rf"{re.escape(label)}\s*:\s*([^\n,]+)"
    m = re.search(pat, text, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "").strip()

def _sanitize_serial(s: str, max_len: int = 60) -> str:
    """
    Try to extract a plausible robot serial from a blob.
    - Prefer Spot-like codes (spot-XXXX...).
    - Else cut at first comma/newline.
    - Finally, hard-truncate to max_len.
    """
    if not s:
        return ""
    s = s.strip()

    # 1) Spot-style pattern
    m = re.search(r"(spot-[A-Za-z0-9_-]+)", s, flags=re.IGNORECASE)
    if m:
        return m.group(1)[:max_len]

    # 2) cut at comma/newline
    s = re.split(r"[\n,]", s, 1)[0].strip()

    # 3) collapse spaces
    s = re.sub(r"\s+", " ", s)

    return s[:max_len]



class Command(BaseCommand):
    help = "Import/Upsert Robots + Payloads from a CSV export (e.g., Notion). Upserts by Serial."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to CSV exported from Notion")
        parser.add_argument("--dry-run", action="store_true", help="Parse and show counts but do not write DB")
        parser.add_argument("--encoding", default="utf-8-sig",
                            help="File encoding (utf-8-sig handles Notion's BOM).")
        parser.add_argument("--delimiter", default=",", help="CSV delimiter (default ,)")
        parser.add_argument("--payload-seps", default=",;", help="Separators for payload lists")
        parser.add_argument("--licenses-seps", default=",;", help="Separators for license lists")

        # Column mappings (match your CSV header names exactly; override as needed)
        parser.add_argument("--col-model", default="Model")
        parser.add_argument("--col-serial", default="Serial")
        parser.add_argument("--col-site", default="Site")
        parser.add_argument("--col-location", default="Deployment Location")
        parser.add_argument("--col-tier", default="Tier")
        parser.add_argument("--col-status", default="Status")
        parser.add_argument("--col-robot-type", default="Robot Type")   # sometimes "Type"
        parser.add_argument("--col-licenses", default="License Numbers")
        parser.add_argument("--col-payloads", default="Payloads")
        parser.add_argument("--col-manager-name", default="Manager Name")
        parser.add_argument("--col-manager-email", default="Manager Email")
        parser.add_argument("--col-slack", default="Slack Channel")

        parser.add_argument("--preview", type=int, default=0,
                            help="Show first N parsed rows and exit (no DB writes).")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["csv_path"]
        if not os.path.exists(path):
            raise CommandError(f"CSV not found: {path}")

        dry = bool(opts.get("dry_run"))
        delimiter = opts["delimiter"]
        encoding = opts["encoding"]
        payload_seps = opts["payload_seps"]
        license_seps = opts["licenses_seps"]
        preview = int(opts["preview"] or 0)

        # Normalize mapping keys to underscores
        col: dict[str, str] = {}
        for k, v in opts.items():
            if k.startswith("col_"):
                key = k.replace("col_", "").replace("-", "_")
                col[key] = v

        created, updated, skipped = 0, 0, 0
        preview_rows: list[dict] = []

        with open(path, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames or []
            if not headers:
                raise CommandError("CSV has no headers.")
            if col["serial"] not in headers:
                raise CommandError(
                    f"CSV is missing required Serial column: {col['serial']!r}. Present headers: {headers}"
                )

            for row in reader:
                # Serial can be a blob column like "Robot Data"
                raw_serial = (row.get(col["serial"]) or "").strip()
                serial = raw_serial
                if not serial or "Serial" in raw_serial:
                    extracted = _extract_labeled(raw_serial, "Serial")
                    if extracted:
                        serial = extracted
                serial = (serial or "").strip()

                if not serial:
                    skipped += 1
                    continue

                model = (row.get(col["model"]) or row.get("Model") or "").strip() or "UNKNOWN"
                site_name = (row.get(col["site"]) or row.get("Site") or "").strip()
                location = (row.get(col["location"]) or row.get("Location") or "").strip()
                tier = (row.get(col["tier"]) or row.get("Tier") or "").strip() or "P2"
                status = (row.get(col["status"]) or row.get("Status") or "").strip() or "active"
                slack_channel = (row.get(col["slack"]) or row.get("Slack Channel") or "").strip()

                robot_type = (
                    row.get(col.get("robot_type", "Robot Type"))
                    or row.get("Robot Type")
                    or row.get("Type")
                    or ""
                ).strip()

                manager_name = (row.get(col["manager_name"]) or row.get("Manager Name") or "").strip()
                manager_email = (row.get(col["manager_email"]) or row.get("Manager Email") or "").strip()

                licenses_raw = (row.get(col["licenses"]) or row.get("License Numbers") or "").strip()
                licenses = _split_multi(licenses_raw, seps=license_seps)

                payloads_raw = (row.get(col["payloads"]) or row.get("Payloads") or "").strip()
                payload_names = _split_multi(payloads_raw, seps=payload_seps)

                if preview and len(preview_rows) < preview:
                    preview_rows.append({
                        "model": model,
                        "serial": serial,
                        "site": site_name,
                        "payloads": payload_names,
                        "tier": tier,
                        "status": status,
                    })

                # Upserts
                site = None
                if site_name:
                    site, _ = Site.objects.get_or_create(name=site_name, defaults={"tz": "UTC"})
                    if slack_channel and site.slack_channel != slack_channel:
                        if not dry:
                            site.slack_channel = slack_channel
                            site.save(update_fields=["slack_channel"])

                manager = None
                if manager_email:
                    manager, _ = Contact.objects.get_or_create(
                        email=manager_email, defaults={"name": manager_name or manager_email}
                    )
                elif manager_name:
                    manager, _ = Contact.objects.get_or_create(name=manager_name)

                defaults = dict(
                    model=model,
                    site=site,
                    tier=tier,
                    status=status,
                    robot_type=robot_type,
                    location=location,
                    environments=[],  # consistent with admin form
                    licenses=licenses,
                    manager=manager,
                )

                try:
                    robot = Robot.objects.get(serial=serial)
                    changed = False
                    for fld, newval in defaults.items():
                        cur = getattr(robot, fld)
                        if fld == "site":
                            cur_id = cur.id if cur else None
                            new_id = newval.id if newval else None
                            if cur_id != new_id:
                                changed = True
                                if not dry:
                                    setattr(robot, fld, newval)
                        elif cur != newval:
                            changed = True
                            if not dry:
                                setattr(robot, fld, newval)
                    if changed and not dry:
                        robot.save()
                    updated += 1 if changed else 0
                except Robot.DoesNotExist:
                    robot = None
                    if not dry:
                        robot = Robot.objects.create(serial=serial, **defaults)
                    created += 1

                if not dry:
                    payload_objs = []
                    for pname in payload_names:
                        if not pname:
                            continue
                        p, _ = Payload.objects.get_or_create(name=pname)
                        payload_objs.append(p)
                    if robot is None:
                        robot = Robot.objects.get(serial=serial)
                    robot.payloads.set(payload_objs)

        if preview_rows:
            for i, pr in enumerate(preview_rows, 1):
                self.stdout.write(f"[{i}] {pr}")
            raise CommandError("Preview finished. No DB changes applied.")

        if dry:
            raise CommandError(f"DRY RUN: created={created}, updated={updated}, skipped={skipped}")

        self.stdout.write(self.style.SUCCESS(
            f"Import complete. created={created}, updated={updated}, skipped={skipped}"
        ))
