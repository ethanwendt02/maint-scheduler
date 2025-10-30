# apps/checklists/migrations/0004_alter_checklistrun_options_and_more.py
from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        ("checklists", "0003_rename_updated_at_checklistrun_created_at"),
        ("auth", "__latest__"),  # safe: only to ensure auth_user exists for FK
    ]

    operations = [
        # --- Make this migration safe on Render where legacy columns may already be gone ---
        migrations.RunSQL(
            sql=r"""
            -- 1) ChecklistRun: drop legacy columns if they still exist
            ALTER TABLE checklists_checklistrun
                DROP COLUMN IF EXISTS notes,
                DROP COLUMN IF EXISTS photos,
                DROP COLUMN IF EXISTS responses,
                DROP COLUMN IF EXISTS tools_used,
                DROP COLUMN IF EXISTS work_order_id;

            -- 2) ChecklistTemplate: drop old columns if they still exist
            ALTER TABLE checklists_checklisttemplate
                DROP COLUMN IF EXISTS checklist_id,
                DROP COLUMN IF EXISTS items,
                DROP COLUMN IF EXISTS kit,
                DROP COLUMN IF EXISTS requires_photos,
                DROP COLUMN IF EXISTS version;

            -- 3) ChecklistRun: add new columns if missing
            ALTER TABLE checklists_checklistrun
                ADD COLUMN IF NOT EXISTS started_at timestamp with time zone,
                ADD COLUMN IF NOT EXISTS completed_at timestamp with time zone,
                ADD COLUMN IF NOT EXISTS created_by_id bigint;

            -- Add FK for created_by if we just created the column (skip if it already exists)
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='checklists_checklistrun' AND column_name='created_by_id'
                )
                AND NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname='checklists_checklistrun_created_by_id_fk'
                )
                THEN
                    ALTER TABLE checklists_checklistrun
                      ADD CONSTRAINT checklists_checklistrun_created_by_id_fk
                      FOREIGN KEY (created_by_id) REFERENCES auth_user(id)
                      DEFERRABLE INITIALLY DEFERRED;
                END IF;
            END$$;

            -- 4) ChecklistTemplate: add description if missing
            ALTER TABLE checklists_checklisttemplate
                ADD COLUMN IF NOT EXISTS description text;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # --- Keep model state in sync with the DB (no-op on DB thanks to IF EXISTS/NOT EXISTS) ---
        migrations.AlterModelOptions(
            name="checklistrun",
            options={"ordering": ("-started_at",), "verbose_name": "Checklist run", "verbose_name_plural": "Checklist runs"},
        ),
        migrations.AlterModelOptions(
            name="checklisttemplate",
            options={"ordering": ("name",), "verbose_name": "Checklist template", "verbose_name_plural": "Checklist templates"},
        ),

        # Model field declarations (Django needs these to know the schema; DB already handled)
        migrations.AddField(
            model_name="checklistrun",
            name="started_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="checklistrun",
            name="completed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="checklistrun",
            name="created_by",
            field=models.ForeignKey(
                null=True, blank=True,
                to=settings.AUTH_USER_MODEL,
                on_delete=models.SET_NULL,
                related_name="created_checklist_runs",
            ),
        ),
        migrations.AddField(
            model_name="checklisttemplate",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),

        # Ensure we still have the latest definition of signed_by (if it remains on the model)
        migrations.AlterField(
            model_name="checklistrun",
            name="signed_by",
            field=models.ForeignKey(
                null=True, blank=True,
                to=settings.AUTH_USER_MODEL,
                on_delete=models.SET_NULL,
                related_name="signed_checklist_runs",
            ),
        ),

        # The new simple items table
        migrations.CreateModel(
            name="ChecklistItem",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("order", models.PositiveIntegerField(default=0)),
                ("text", models.TextField()),
                ("template", models.ForeignKey(on_delete=models.CASCADE, to="checklists.checklisttemplate")),
            ],
            options={"ordering": ("order", "id")},
        ),
    ]
