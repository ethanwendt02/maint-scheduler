# apps/checklists/migrations/0005_fix_schema_idempotent_sqlite_safe.py
from django.db import migrations, models, connection
from django.utils import timezone


def _colnames(table):
    """
    Return a set of existing column names for the given table, for both
    SQLite and Postgres (works on either engine).
    """
    vendor = connection.vendor
    with connection.cursor() as cur:
        if vendor == "sqlite":
            cur.execute(f"PRAGMA table_info('{table}');")
            # rows: cid, name, type, notnull, dflt_value, pk
            return {row[1] for row in cur.fetchall()}
        else:
            # Postgres (and others that support information_schema)
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
            """, [table])
            return {r[0] for r in cur.fetchall()}


def add_template_timestamps(apps, schema_editor):
    """
    Ensure checklists_checklisttemplate has created_at / updated_at columns.
    Do nothing if they already exist. Works for SQLite and Postgres.
    """
    table = "checklists_checklisttemplate"
    cols = _colnames(table)

    vendor = connection.vendor
    with connection.cursor() as cur:
        if "created_at" not in cols:
            if vendor == "sqlite":
                cur.execute(
                    f"ALTER TABLE {table} ADD COLUMN created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP);"
                )
            else:
                cur.execute(
                    f"ALTER TABLE {table} ADD COLUMN created_at timestamptz NOT NULL DEFAULT NOW();"
                )
        if "updated_at" not in cols:
            if vendor == "sqlite":
                cur.execute(
                    f"ALTER TABLE {table} ADD COLUMN updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP);"
                )
            else:
                cur.execute(
                    f"ALTER TABLE {table} ADD COLUMN updated_at timestamptz NOT NULL DEFAULT NOW();"
                )


def backfill_started_at(apps, schema_editor):
    """
    Set started_at = NOW() where it is NULL so we can enforce NOT NULL.
    """
    with connection.cursor() as cur:
        cur.execute("""
            UPDATE checklists_checklistrun
               SET started_at = CURRENT_TIMESTAMP
             WHERE started_at IS NULL
        """)


class Migration(migrations.Migration):

    dependencies = [
        ("checklists", "0004_alter_checklistrun_options_and_more"),
    ]

    operations = [
        # 1) Ensure template timestamps exist at the database level
        migrations.RunPython(add_template_timestamps, reverse_code=migrations.RunPython.noop),

        # 2) Backfill started_at so we can make it NOT NULL cleanly
        migrations.RunPython(backfill_started_at, reverse_code=migrations.RunPython.noop),

        # 3) Reflect created_at/updated_at on ChecklistTemplate in Django state
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

        # 4) Enforce NOT NULL + default on started_at going forward
        migrations.AlterField(
            model_name="checklistrun",
            name="started_at",
            field=models.DateTimeField(default=timezone.now, null=False),
        ),
    ]
