from django.db import migrations


def force_text_columns(apps, schema_editor):
    # Only run on Postgres (Render)
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        "ALTER TABLE checklists_checklistitem ALTER COLUMN text TYPE text;"
    )
    schema_editor.execute(
        "ALTER TABLE checklists_checklistitem ALTER COLUMN kit_items TYPE text;"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("checklists", "0013_widen_checklistitem_text"),  # change to your latest
    ]

    operations = [
        migrations.RunPython(force_text_columns, migrations.RunPython.noop),
    ]
