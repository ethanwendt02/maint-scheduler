# apps/notifications/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from typing import List, Optional
from .utils import send_slack, send_email

CHANNEL_SLACK = "slack"
CHANNEL_EMAIL = "email"
STATUS_QUEUED = "queued"
STATUS_SENT   = "sent"
STATUS_FAILED = "failed"

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

    # Existing linkage
    work_order_id = models.IntegerField(blank=True, null=True)

    # 🔗 NEW: deep links
    checklist_run     = models.ForeignKey("checklists.ChecklistRun", null=True, blank=True, on_delete=models.SET_NULL)
    checklist_template= models.ForeignKey("checklists.ChecklistTemplate", null=True, blank=True, on_delete=models.SET_NULL)
    maintenance_policy= models.ForeignKey("policies.MaintenancePolicy", null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

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
    def _as_text_for_slack(self) -> str:
        subj = (self.subject or "").strip()
        body = (self.message or "").strip()
        lines = []
        if subj:
            lines.append(f"*{subj}*")
        if body:
            lines.append(body)
        return "\n".join(lines) or "(no content)"

    def _as_slack_blocks(self) -> Optional[list]:
        """
        Build a Block Kit payload that includes links to checklist run/template/policy when present.
        Works for Incoming Webhooks and chat.postMessage alike.
        """
        label = (self.to or "#maintenance-scheduler").strip()
        blocks = []

        # Title & body
        title = (self.subject or "").strip()
        body = (self.message or "").strip()
        if title:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*"}})
        if body:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": body}})

        # Links row
        fields = []

        # Checklist Run link (Admin)
        if self.checklist_run_id:
            run_label = f"Run #{self.checklist_run_id}"
            link = self._admin_link("checklists", "checklistrun", self.checklist_run_id, run_label)
            if link:
                fields.append({"type": "mrkdwn", "text": f"*Checklist Run:*\n{link}"})

        # Checklist Template link (Admin)
        if self.checklist_template_id:
            tpl_label = str(self.checklist_template)[:60]
            link = self._admin_link("checklists", "checklisttemplate", self.checklist_template_id, tpl_label)
            if link:
                fields.append({"type": "mrkdwn", "text": f"*Template:*\n{link}"})

        # Maintenance Policy link (Admin)
        if self.maintenance_policy_id:
            pol_label = str(self.maintenance_policy)[:60]
            link = self._admin_link("policies", "maintenancepolicy", self.maintenance_policy_id, pol_label)
            if link:
                fields.append({"type": "mrkdwn", "text": f"*Policy:*\n{link}"})

        # Optional: Work Order id (no FK in your model yet)
        if self.work_order_id:
            # Admin change URL if you later add FK; for now, plain text
            fields.append({"type": "mrkdwn", "text": f"*Work Order:*\n#{self.work_order_id}"})

        if fields:
            blocks.append({"type": "section", "fields": fields})

        # Label / context
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"Posted from Maintenance Scheduler • {label}"}]})

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
                label = (self.to or "#maintenance-scheduler").strip()
                text = self._as_text_for_slack()
                blocks = self._as_slack_blocks()
                ok = send_slack(label, text, blocks=blocks)  # 🔥 now sends Block Kit
                if ok:
                    self._mark(STATUS_SENT)
                    return True
                else:
                    self._mark(STATUS_FAILED, "Slack webhook failed or not configured")
                    return False

            self._mark(STATUS_FAILED, f"Unknown channel '{self.channel}'")
            return False

        except Exception as e:
            self._mark(STATUS_FAILED, str(e))
            return False

