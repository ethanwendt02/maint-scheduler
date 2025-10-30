from django.conf import settings
from django.db import migrations, models


RUNSQL_SAFE = migrations.RunSQL(
    sql=r"""
    -- ===== ChecklistRun: remove legacy columns if present =====
    ALTER TABLE checklists_checklistrun
        DROP COLUMN IF EXISTS notes,
        DROP COLUMN IF EXISTS photos,
        DROP COLUMN IF EXISTS responses,
        DROP COLUMN IF EXISTS tools_used,
        DROP COLUMN IF EXISTS work_order_id;

    -- ===== ChecklistTemplate: remove legacy columns if present =====
    ALTER TABLE checklists_checklisttemplate
        DROP COLUMN IF EXISTS checklist_id,
        DROP COLUMN IF EXISTS items,
        DROP COLUMN IF EXISTS kit,
        DROP COLUMN IF EXISTS requires_photos,
        DROP COLUMN IF EXISTS version;

    -- ===== ChecklistRun: add new columns if missing =====
    ALTER TABLE checklists_checklistrun
        ADD COLUMN IF NOT EXISTS started_at timestamp with time zone,
        ADD COLUMN IF NOT EXISTS completed_at timestamp with time zone,
        ADD COLUMN IF NOT EXISTS created_by_id bigint;

    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='checklists_checklistrun' AND column_name='created_by_id'
        ) AND NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname='checklists_checklistrun_created_by_id_fk'
        ) THEN
            ALTER TABLE checklists_checklistrun
              ADD CONSTRAINT checklists_checklistrun_created_by_id_fk
              FOREIGN KEY (created_by_id) REFERENCES auth_user(id)
              DEFERRABLE INITIALLY DEFERRED;
        END IF;
    END$$;

    -- ===== ChecklistTemplate: add description if missing =====
    ALTER TABLE checklists_checklisttemplate
        ADD COLUMN IF NOT EXISTS description text;

    -- ===== ChecklistTemplate: ensure created_at/updated_at exist for admin/importers =====
    ALTER TABLE checklists_checklisttemplate
        ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();

    -- if we just added defaults, drop the defaults to match typical auto_now/_add behavior
    ALTER TABLE checklists_checklisttemplate
        ALTER COLUMN created_at DROP DEFAULT,
        ALTER COLUMN updated_at DROP DEFAULT;

    -- ===== ChecklistItem table (minimal) if not already present =====
    CREATE TABLE IF NOT EXISTS checklists_checklistitem (
        id bigserial PRIMARY KEY,
        "order" integer NOT NULL DEFAULT 0,
        text text NOT NULL,
        template_id bigint NOT NULL REFERENCES checklists_checklisttemplate(id) ON DELETE CASCADE
    );

    -- simple index for template_id (IF NOT EXISTS via name check)
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'checklists_checklistitem_template_id_idx'
        ) THEN
            CREATE INDEX checklists_checklistitem_template_id_idx
                ON checklists_checklistitem(template_id);
        END IF;
    END$$;
    """,
    reverse_sql=migrations.RunSQL.noop,
)


class Migration(migrations.Migration):
    dependencies = [
        ("checklists", "0003_rename_updated_at_checklistrun_created_at"),
    ]

    operations = [
        # 1) Do idempotent SQL first
        RUNSQL_SAFE,

        # 2) Update Django's idea of the models WITHOUT issuing SQL again
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelOptions(
                    name="checklistrun",
                    options={
                        "ordering": ("-started_at",),
                        "verbose_name": "Checklist run",
                        "verbose_name_plural": "Checklist runs",
                    },
                ),
                migrations.AlterModelOptions(
                    name="checklisttemplate",
                    options={
                        "ordering": ("name",),
                        "verbose_name": "Checklist template",
                        "verbose_name_plural": "Checklist templates",
                    },
                ),

                # Reflect the columns that now (may already) exist in DB:
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
                migrations.AddField(
                    model_name="checklisttemplate",
                    name="description",
                    field=models.TextField(blank=True, default=""),
                ),
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

                # Model for ChecklistItem (state only – table is created above if needed)
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
            ],
        ),
    ]
