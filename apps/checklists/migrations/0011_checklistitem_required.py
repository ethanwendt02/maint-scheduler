from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checklists", "0010_chekclistitem_required.py"),  # <-- keep whatever dependency Django generated
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Column already exists in prod DB, but this makes it safe everywhere
                migrations.RunSQL(
                    "ALTER TABLE checklists_checklistitem "
                    "ADD COLUMN IF NOT EXISTS required boolean;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # Backfill any NULLs just in case
                migrations.RunSQL(
                    "UPDATE checklists_checklistitem "
                    "SET required = TRUE "
                    "WHERE required IS NULL;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # Ensure default + not-null (safe if already set)
                migrations.RunSQL(
                    "ALTER TABLE checklists_checklistitem "
                    "ALTER COLUMN required SET DEFAULT TRUE;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "ALTER TABLE checklists_checklistitem "
                    "ALTER COLUMN required SET NOT NULL;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                # This updates Django’s model state without “adding” the column again
                migrations.AddField(
                    model_name="checklistitem",
                    name="required",
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]
