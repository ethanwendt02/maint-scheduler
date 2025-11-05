# apps/checklists/migrations/0008_pg_idempotent_cleanup.py
from django.db import migrations

PG_SQL = """
-- Make legacy drops idempotent on Postgres
-- ChecklistRun legacy fields
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS notes CASCADE;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS photos CASCADE;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS responses CASCADE;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS tools_used CASCADE;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS work_order_id CASCADE;

-- ChecklistTemplate legacy fields
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS checklist_id CASCADE;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS items CASCADE;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS kit CASCADE;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS requires_photos CASCADE;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS version CASCADE;

-- Ensure template timestamps exist (harmless if already present)
ALTER TABLE checklists_checklisttemplate
  ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();
ALTER TABLE checklists_checklisttemplate
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
"""

class Migration(migrations.Migration):
    dependencies = [
        ("checklists", "0007_alter_checklistitem_options_and_more"),
    ]

    operations = [
        # Only run on Postgres; on SQLite/MySQL this block is a no-op
        migrations.RunSQL(sql=PG_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
