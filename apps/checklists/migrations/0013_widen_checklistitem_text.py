# apps/checklists/migrations/000X_widen_checklistitem_text.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checklists", "0012_checklistitem_kit_items"),  # <-- change this
    ]

    operations = [
        migrations.AlterField(
            model_name="checklistitem",
            name="text",
            field=models.TextField(),
        ),
        # Optional: if section might exceed 120 for you, bump it safely:
         migrations.AlterField(
             model_name="checklistitem",
             name="section",
             field=models.CharField(max_length=255, blank=True, db_index=True, default=""),
         ),
    ]