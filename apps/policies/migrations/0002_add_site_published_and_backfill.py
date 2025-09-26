from django.db import migrations, models
import django.db.models.deletion

def backfill_site_from_scope(apps, schema_editor):
    Policy = apps.get_model("policies", "MaintenancePolicy")
    Site = apps.get_model("fleet", "Site")
    for p in Policy.objects.all():
        if getattr(p, "site_id", None):
            continue
        scope = getattr(p, "scope", None) or {}
        site_name = None
        try:
            site_name = scope.get("site")
        except Exception:
            site_name = None
        if site_name:
            site = Site.objects.filter(name=site_name).first()
            if site:
                p.site = site
                p.save(update_fields=["site"])

class Migration(migrations.Migration):

    # IMPORTANT: set these to migrations that actually exist in your project
    dependencies = [
        ("policies", "0001_initial"),
        ("fleet", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancepolicy",
            name="site",
            field=models.ForeignKey(
                related_name="policies",
                on_delete=django.db.models.deletion.CASCADE,
                to="fleet.site",
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="maintenancepolicy",
            name="published",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_site_from_scope, migrations.RunPython.noop),
    ]
