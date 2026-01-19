from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checklists", "0010_checklistrun_completed_pdf"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # DB already has the column in production, so do nothing here.
            ],
            state_operations=[
                migrations.AddField(
                    model_name="checklistitem",
                    name="required",
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]
