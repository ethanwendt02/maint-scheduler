from django.db import migrations, models
from django.utils import timezone

ADD_TEMPLATE_TIMESTAMPS_SQL = """
ALTER TABLE checklists_checklisttemplate
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT NOW();
"""

BACKFILL_STARTED_AT_SQL = """
UPDATE checklists_checklistrun
   SET started_at = NOW()
 WHERE started_at IS NULL;
"""

class Migration(migrations.Migration):
    dependencies = [
        ("checklists", "0004_alter_checklistrun_options_and_more"),
    ]

    operations = [
        # 1) Create created_at / updated_at on ChecklistTemplate if missing (safe to re-run)
        migrations.RunSQL(ADD_TEMPLATE_TIMESTAMPS_SQL, reverse_sql=""),

        # 2) Backfill NULL started_at so we can make it NOT NULL without an interactive prompt
        migrations.RunSQL(BACKFILL_STARTED_AT_SQL, reverse_sql=""),

        # 3) Tell Django those two timestamp fields exist (so admin/forms know about them)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="checklisttemplate",
                    name="created_at",
                    field=models.DateTimeField(auto_now_add=True),
                ),
                migrations.AddField(
                    model_name="checklisttemplate",
                    name="updated_at",
                    field=models.DateTimeField(auto_now=True),
                ),
            ],
        ),

        # 4) Lock down started_at to be required going forward with a sensible default
        migrations.AlterField(
            model_name="checklistrun",
            name="started_at",
            field=models.DateTimeField(default=timezone.now, null=False),
        ),
    ]
