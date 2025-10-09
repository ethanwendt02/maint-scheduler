import os, time, typing as t, requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.fleet.models import Robot, Site, Payload, Contact

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

def _prop_str(props: dict, name: str) -> str:
    if not name or name not in props:
        return ""
    p = props[name]; tpe = p.get("type")
    if tpe == "title":
        return "".join([r.get("plain_text","") for r in p["title"]]).strip()
    if tpe == "rich_text":
        return "".join([r.get("plain_text","") for r in p["rich_text"]]).strip()
    if tpe == "select":
        return (p["select"]["name"] if p["select"] else "") or ""
    if tpe == "url":
        return p.get("url") or ""
    if tpe == "number":
        val = p.get("number")
        return "" if val is None else str(val)
    if tpe == "email":
        return p.get("email") or ""
    if tpe == "checkbox":
        return "true" if p.get("checkbox") else "false"
    if tpe == "people":
        # join names as a fallback
        return ",".join([u.get("name") or u.get("id") for u in p.get("people", [])])
    return ""

def _prop_list(props: dict, name: str) -> t.List[str]:
    if not name or name not in props:
        return []
    p = props[name]; tpe = p.get("type")
    if tpe == "multi_select":
        return [opt["name"] for opt in p.get("multi_select", [])]
    if tpe in ("rich_text", "title"):
        # allow comma/semicolon separated text
        raw = _prop_str(props, name)
        return [x.strip() for x in re_split(raw)]
    return []

def _prop_people(props: dict, name: str) -> t.List[dict]:
    if not name or name not in props:
        return []
    p = props[name]
    if p.get("type") != "people":
        return []
    result = []
    for u in p.get("people", []):
        # Notion may or may not include email; name usually present
        person = {"name": u.get("name") or "", "id": u.get("id") or ""}
        person["email"] = (u.get("person") or {}).get("email") or ""
        result.append(person)
    return result

def re_split(s: str) -> t.List[str]:
    import re
    return re.split(r"[;,]", s) if s else []

def notion_query_db(token: str, db_id: str) -> t.Iterable[dict]:
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}
    url = f"{NOTION_API_BASE}/databases/{db_id}/query"
    payload = {"page_size": 100}
    next_cursor = None
    while True:
        if next_cursor:
            payload["start_cursor"] = next_cursor
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise CommandError(f"Notion query failed: {resp.status_code} {resp.text}")
        data = resp.json()
        for page in data.get("results", []):
            yield page
        next_cursor = data.get("next_cursor")
        if not next_cursor:
            break
        time.sleep(0.2)

class Command(BaseCommand):
    help = "Sync robots & related data from a Notion database."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--db-id", help="override NOTION_ROBOT_DB_ID")
        parser.add_argument("--token", help="override NOTION_API_TOKEN")

        # Column mappings (override with your exact Notion field names)
        parser.add_argument("--col-model", default="Model")
        parser.add_argument("--col-serial", default="Serial")
        parser.add_argument("--col-site", default="Site")
        parser.add_argument("--col-location", default="Location")      # within site
        parser.add_argument("--col-tier", default="Tier")
        parser.add_argument("--col-status", default="Status")
        parser.add_argument("--col-robot-type", default="Robot Type")
        parser.add_argument("--col-licenses", default="License Numbers")   # multi or comma text
        parser.add_argument("--col-payloads", default="Payloads")          # multi-select
        parser.add_argument("--col-manager-people", default="Manager")     # people
        parser.add_argument("--col-manager-name", default="Manager Name")  # text fallback
        parser.add_argument("--col-manager-email", default="Manager Email")# email fallback
        parser.add_argument("--col-slack", default="Slack Channel")        # on Site

    @transaction.atomic
    def handle(self, *args, **opts):
        import re
        token = opts.get("token") or os.getenv("NOTION_API_TOKEN")
        db_id = opts.get("db_id") or os.getenv("NOTION_ROBOT_DB_ID")
        if not token or not db_id:
            raise CommandError("NOTION_API_TOKEN and NOTION_ROBOT_DB_ID must be set (env or CLI).")

        dry = opts["dry_run"]

        col = {k.replace("col_", ""): v for k, v in opts.items() if k.startswith("col_")}

        created_r, updated_r, skipped_r = 0, 0, 0

        for page in notion_query_db(token, db_id):
            props = page.get("properties", {})

            model = _prop_str(props, col["model"])
            serial = _prop_str(props, col["serial"])
            if not serial:
                skipped_r += 1
                continue

            site_name = _prop_str(props, col["site"])
            location = _prop_str(props, col["location"])
            tier = _prop_str(props, col["tier"]) or "P2"
            status = _prop_str(props, col["status"]) or "active"
            slack_channel = _prop_str(props, col["slack"])

            robot_type = _prop_str(props, col["robot-type"])
            licenses = _prop_list(props, col["licenses"]) or re_split(_prop_str(props, col["licenses"]))
            licenses = [x for x in [s.strip() for s in licenses] if x]

            payload_names = _prop_list(props, col["payloads"])
            mgr_people = _prop_people(props, col["manager-people"])
            mgr_name = _prop_str(props, col["manager-name"])
            mgr_email = _prop_str(props, col["manager-email"])

            # Upsert Site
            site = None
            if site_name:
                site, _ = Site.objects.get_or_create(name=site_name, defaults={"tz": "UTC"})
                if slack_channel and site.slack_channel != slack_channel:
                    if not dry:
                        site.slack_channel = slack_channel
                        site.save(update_fields=["slack_channel"])

            # Upsert Manager Contact
            manager = None
            if mgr_people:
                # prefer first person
                cand = mgr_people[0]
                m_email = cand.get("email") or mgr_email or ""
                m_name = cand.get("name") or mgr_name or ""
                if m_email:
                    manager, _ = Contact.objects.get_or_create(email=m_email, defaults={"name": m_name or m_email})
                elif m_name:
                    manager, _ = Contact.objects.get_or_create(name=m_name)
            elif mgr_email or mgr_name:
                if mgr_email:
                    manager, _ = Contact.objects.get_or_create(email=mgr_email, defaults={"name": mgr_name or mgr_email})
                else:
                    manager, _ = Contact.objects.get_or_create(name=mgr_name)

            # Upsert/resolve Payloads
            payload_objs = []
            for pname in payload_names:
                po, _ = Payload.objects.get_or_create(name=pname)
                payload_objs.append(po)

            defaults = {
                "model": model or "UNKNOWN",
                "site": site,
                "tier": tier,
                "environment": {},  # keep old path for env flags if you use them elsewhere
                "status": status,
                "robot_type": robot_type,
                "location": location,
                "licenses": licenses,
                "manager": manager,
            }

            try:
                obj = Robot.objects.get(serial=serial)
                changed = []
                for field, val in defaults.items():
                    cur = getattr(obj, field)
                    if field == "site":
                        if (cur.id if cur else None) != (val.id if val else None):
                            changed.append((field, cur, val))
                    elif cur != val:
                        changed.append((field, cur, val))
                if changed:
                    if not dry:
                        for field, _, val in changed:
                            setattr(obj, field, val)
                        obj.save()
                    updated_r += 1
                else:
                    skipped_r += 1
            except Robot.DoesNotExist:
                if not dry:
                    obj = Robot.objects.create(serial=serial, **defaults)
                else:
                    obj = None
                created_r += 1

            # Sync M2M payloads after we have a Robot instance (skip in dry-run)
            if not dry and obj is not None:
                obj.payloads.set(payload_objs)

        self.stdout.write(self.style.SUCCESS(
            f"Done. created={created_r} updated={updated_r} unchanged/skipped={skipped_r} dry_run={dry}"
        ))
