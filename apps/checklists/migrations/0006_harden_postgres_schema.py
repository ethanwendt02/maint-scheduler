from django.db import migrations

SQL = """
-- === ChecklistRun: drop legacy columns only if they exist ===
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS notes;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS photos;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS responses;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS tools_used;
ALTER TABLE checklists_checklistrun DROP COLUMN IF EXISTS work_order_id;

-- === ChecklistTemplate: drop legacy columns only if they exist ===
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS checklist_id;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS items;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS kit;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS requires_photos;
ALTER TABLE checklists_checklisttemplate DROP COLUMN IF EXISTS version;

-- === ChecklistItem: ensure the new column exists and is NOT NULL (no default afterwards) ===
ALTER TABLE checklists_checklistitem
  ADD COLUMN IF NOT EXISTS section varchar(120) NOT NULL DEFAULT '';
ALTER TABLE checklists_checklistitem
  ALTER COLUMN section DROP DEFAULT;
"""

class Migration(migrations.Migration):
    # IMPORTANT: make it depend on 0005 (the last one Render shows)
    dependencies = [
        ("checklists", "0005_fix_schema_idempotent_sqlite_safe"),
    ]
    operations = [
        migrations.RunSQL(SQL),
    ]
