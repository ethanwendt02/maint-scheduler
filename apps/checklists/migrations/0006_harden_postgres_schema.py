# apps/checklists/migrations/0006_harden_postgres_schema.py
from django.db import migrations

def safe_harden(apps, schema_editor):
    conn = schema_editor.connection
    cur = conn.cursor()

    def has_col(table, col):
        # Works on SQLite and Postgres
        if conn.vendor == "sqlite":
            cur.execute(f"PRAGMA table_info('{table}')")
            return any(r[1] == col for r in cur.fetchall())
        else:
            cur.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name=%s AND column_name=%s
                """, [table, col])
            return cur.fetchone() is not None

    def drop_col(table, col):
        if not has_col(table, col):
            return
        if conn.vendor == "sqlite":
            # SQLite ≥ 3.35 supports DROP COLUMN
            cur.execute(f'ALTER TABLE "{table}" DROP COLUMN "{col}"')
        else:
            cur.execute(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS "{col}"')

    def add_col_if_missing(table, col_name, col_def_sql):
        if not has_col(table, col_name):
            cur.execute(f'ALTER TABLE "{table}" ADD COLUMN {col_def_sql}')

    # ChecklistRun: remove legacy columns if they exist
    for col in ["notes", "photos", "responses", "tools_used", "work_order_id"]:
        drop_col("checklists_checklistrun", col)

    # ChecklistTemplate: remove legacy columns if they exist
    for col in ["checklist_id", "items", "kit", "requires_photos", "version"]:
        drop_col("checklists_checklisttemplate", col)

    # ChecklistItem: ensure new column exists
    # Keep DEFAULT '' on SQLite (dropping defaults is awkward there; harmless to keep)
    add_col_if_missing(
        "checklists_checklistitem",
        "section",
        "section varchar(120) NOT NULL DEFAULT ''"
    )

class Migration(migrations.Migration):
    dependencies = [
        ("checklists", "0005_fix_schema_idempotent_sqlite_safe"),
    ]
    operations = [
        migrations.RunPython(safe_harden, migrations.RunPython.noop),
    ]
