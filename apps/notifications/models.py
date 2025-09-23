# apps/notifications/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from typing import List, Optional
from .utils import send_slack, send_email

# --- constants ---------------------------------------------------------------
CHANNEL_SLACK = "slack"
CHANNEL_EMAIL = "email"

STATUS_QUEUED = "queued"
STATUS_SENT   = "sent"
STATUS_FAILED = "failed"

DEFAULT_SLACK_LABEL = "#maintenance-scheduler"  # label prefix shown in Slack message

# --- model -------------------------------------------------------------------
class NotificationLog(models.Model):
    CHANNEL_CHOICES = [(CHANNEL_SLACK, "Slack"), (CHANNEL_EMAIL, "Email")]
    STATUS_CHOICES  = [(STATUS_QUEUED, "Queued"), (STATUS_SENT, "Sent"), (STATUS_FAILED, "Failed")]

    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    to = models.CharField(max_length=255, blank=True, default="")          # email or Slack label (for webhook)
    subject = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True, default="")
    payload = models.JSONField(blank=True, null=True)                      # any extra context
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    error = models.TextField(blank=True, default="")

    # Optional linkage to your domain objects
    work_order_id = models.IntegerField(blank=True, null=True)

    # 🔗 Linked records to surface in Slack
    checklist_run      = models.ForeignKey("checklists.ChecklistRun",      null=True, blank=True, on_delete=models.SET_NULL)
    checklist_template = models.ForeignKey("checklists.ChecklistTemplate", null=True, blank=True, on_delete=models.SET_NULL)
    maintenance_policy = models.ForeignKey("policies.MaintenancePolicy",   null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["channel", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        tag = f"{self.channel}:{self.to or '-'}"
        preview = (self.subject or self.message or "")[:40]
        return f"[{self.status}] {tag} — {preview}"

    # ---------- URL helpers ----------
    def _abs(self, path: str) -> str:
        """
        Build an absolute URL using SITE_BASE_URL if set, otherwise return the path.
        Set SITE_BASE_URL in env (e.g., https://maint-scheduler.onrender.com).
        """
        base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
        return f"{base}{path}" if base else path

    def _admin_link(self, app: str, model: str, pk: int, label: str) -> Optional[str]:
        try:
            path = reverse(f"admin:{app}_{model}_change", args=[pk])  # e.g., admin:checklists_checklistrun_change
            url = self._abs(path)
            return f"<{url}|{label}>"
        except Exception:
            return None

       # ---------- Slack formatting ----------
    def _fmt_dt(self, dt) -> str:
        if not dt:
            return "—"
        try:
            from django.utils import timezone
            return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(dt)

    def _guess(self, obj, names):
        """Try attributes/methods in order; return first non-empty value."""
        for name in names:
            if hasattr(obj, name):
                val = getattr(obj, name)
                try:
                    return val() if callable(val) else val
                except Exception:
                    continue
        return None

    def _field(self, label: str, value: str) -> dict:
        return {"type": "mrkdwn", "text": f"*{label}:*\n{value}"}

    def _buttons_row(self, buttons: list[dict]) -> dict:
        """buttons: list of {'text': 'Open Run', 'url': 'https://...'}"""
        return {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": b["text"]}, "url": b["url"]}
                for b in buttons if b.get("url")
            ],
        }

    def _as_text_for_slack(self) -> str:
        subj = (self.subject or "").strip()
        body = (self.message or "").strip()
        lines: List[str] = []
        if subj:
            lines.append(f"*{subj}*")
        if body:
            lines.append(body)
        return "\n".join(lines) or "(no content)"

    def _blocks_for_run(self) -> list:
        if not self.checklist_run_id:
            return []
        run = self.checklist_run  # FK is already loaded by Django when accessed
        blocks = []

        # Admin link
        run_link = self._admin_link("checklists", "checklistrun", self.checklist_run_id, f"Run #{self.checklist_run_id}")

        # Heuristic fields (adjust names if your models differ)
        status   = self._guess(run, ["get_status_display", "status"]) or "—"
        robot    = self._guess(run, ["robot", "device", "asset"]) or "—"
        site     = self._guess(run, ["site", "location"]) or "—"
        started  = self._fmt_dt(self._guess(run, ["started_at", "start_time", "created_at", "created_on"]))
        finished = self._fmt_dt(self._guess(run, ["completed_at", "finished_at", "updated_at"]))

        # Progress (try common patterns; falls back gracefully)
        steps_total = self._guess(run, ["steps_total", "total_steps", "items_count"])
        steps_done  = self._guess(run, ["steps_completed", "completed_steps", "done_count"])
        progress    = "—"
        try:
            if isinstance(steps_total, int) and steps_total > 0 and isinstance(steps_done, int):
                pct = int((steps_done / steps_total) * 100)
                progress = f"{steps_done}/{steps_total} ({pct}%)"
        except Exception:
            pass

        fields = [
            self._field("Checklist Run", run_link or f"#{self.checklist_run_id}"),
            self._field("Status", str(status)),
            self._field("Robot", str(robot)),
            self._field("Site", str(site)),
            self._field("Started", started),
            self._field("Completed", finished),
        ]
        if progress != "—":
            fields.append(self._field("Progress", progress))

        blocks.append({"type": "section", "fields": fields})

        # Row of buttons (static links work fine with webhooks)
        buttons = []
        if run_link:
            # run_link is <url|label>; extract URL between <>
            try:
                url = run_link.split("<", 1)[1].split("|", 1)[0]
                buttons.append({"text": "Open Run", "url": url})
            except Exception:
                pass
        blocks.append(self._buttons_row(buttons))
        return blocks

    def _blocks_for_template(self) -> list:
        if not self.checklist_template_id:
            return []
        tpl = self.checklist_template
        blocks = []

        tpl_link = self._admin_link("checklists", "checklisttemplate", self.checklist_template_id, str(tpl)[:60])

        version = self._guess(tpl, ["version", "revision"]) or "—"
        updated = self._fmt_dt(self._guess(tpl, ["updated_at", "modified_at"]))
        step_count = self._guess(tpl, ["steps_count", "items_count"])
        if not isinstance(step_count, int):
            step_count = "—"

        fields = [
            self._field("Template", tpl_link or str(tpl)[:60]),
            self._field("Version", str(version)),
            self._field("Steps", str(step_count)),
            self._field("Updated", updated),
        ]
        blocks.append({"type": "section", "fields": fields})

        buttons = []
        if tpl_link:
            try:
                url = tpl_link.split("<", 1)[1].split("|", 1)[0]
                buttons.append({"text": "Open Template", "url": url})
            except Exception:
                pass
        blocks.append(self._buttons_row(buttons))
        return blocks

    def _blocks_for_policy(self) -> list:
        if not self.maintenance_policy_id:
            return []
        pol = self.maintenance_policy
        blocks = []

        pol_link = self._admin_link("policies", "maintenancepolicy", self.maintenance_policy_id, str(pol)[:60])

        interval = self._guess(pol, ["interval", "frequency", "cadence"]) or "—"
        next_due = self._fmt_dt(self._guess(pol, ["next_due", "next_run_at", "due_date"]))
        scope    = self._guess(pol, ["scope", "applies_to"]) or "—"

        fields = [
            self._field("Policy", pol_link or str(pol)[:60]),
            self._field("Interval", str(interval)),
            self._field("Next due", next_due),
            self._field("Scope", str(scope)),
        ]
        blocks.append({"type": "section", "fields": fields})

        buttons = []
        if pol_link:
            try:
                url = pol_link.split("<", 1)[1].split("|", 1)[0]
                buttons.append({"text": "Open Policy", "url": url})
            except Exception:
                pass
        blocks.append(self._buttons_row(buttons))
        return blocks

    def _as_slack_blocks(self) -> Optional[list]:
        """
        Pretty Block Kit layout with title/body, rich summaries for Run/Template/Policy,
        and a context footer. Safe even if some fields don't exist.
        """
        label = (self.to or DEFAULT_SLACK_LABEL).strip()
        blocks: list = []

        # Title & body
        title = (self.subject or "").strip()
        body  = (self.message or "").strip()
        if title:
            blocks.append({"type": "header", "text": {"type": "plain_text", "text": title}})
        if body:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": body}})

        # Details
        any_detail = False
        rb = self._blocks_for_run()
        if rb:
            any_detail = True
            blocks.append({"type": "divider"})
            blocks.extend(rb)

        tb = self._blocks_for_template()
        if tb:
            any_detail = True
            blocks.append({"type": "divider"})
            blocks.extend(tb)

        pb = self._blocks_for_policy()
        if pb:
            any_detail = True
            blocks.append({"type": "divider"})
            blocks.extend(pb)

        # Footer/context
        if any_detail:
            blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Posted from Maintenance Scheduler • {label}"}],
        })

        return blocks or None

    # ---------- state helpers ----------
    def _mark(self, status: str, error_msg: str = "") -> None:
        self.status = status
        self.error = error_msg
        if status == STATUS_SENT and not self.sent_at:
            self.sent_at = timezone.now()
        self.save(update_fields=["status", "error", "sent_at"])

    # ---------- main API ----------
    def send(self) -> bool:
        try:
            if self.channel == CHANNEL_EMAIL:
                recipients: List[str] = [e.strip() for e in (self.to or "").split(",") if e.strip()]
                send_email(recipients, self.subject or "(no subject)", self.message or "")
                self._mark(STATUS_SENT)
                return True

            if self.channel == CHANNEL_SLACK:
                label  = (self.to or DEFAULT_SLACK_LABEL).strip()
                text   = self._as_text_for_slack()
                blocks = self._as_slack_blocks()
                ok = send_slack(label, text, blocks=blocks)  # supports Block Kit via webhook
                if ok:
                    self._mark(STATUS_SENT)
                    return True
                self._mark(STATUS_FAILED, "Slack webhook failed or not configured")
                return False

            self._mark(STATUS_FAILED, f"Unknown channel '{self.channel}'")
            return False

        except Exception as e:
            self._mark(STATUS_FAILED, str(e))
            return False


