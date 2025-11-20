from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("checklists", "0006_harden_postgres_schema"),
    ]

    operations = [
        # 1) Remove the old JSON/legacy fields **in migration state only**.
        #    database_operations=[] means no SQL is executed, which is safe
        #    because those columns have already been dropped on Postgres.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name="checklistrun",
                    name="notes",
                ),
                migrations.RemoveField(
                    model_name="checklistrun",
                    name="photos",
                ),
                migrations.RemoveField(
                    model_name="checklistrun",
                    name="responses",
                ),
                migrations.RemoveField(
                    model_name="checklistrun",
                    name="tools_used",
                ),
                migrations.RemoveField(
                    model_name="checklistrun",
                    name="work_order",
                ),
                migrations.RemoveField(
                    model_name="checklisttemplate",
                    name="checklist_id",
                ),
                migrations.RemoveField(
                    model_name="checklisttemplate",
                    name="items",
                ),
                migrations.RemoveField(
                    model_name="checklisttemplate",
                    name="kit",
                ),
                migrations.RemoveField(
                    model_name="checklisttemplate",
                    name="requires_photos",
                ),
                migrations.RemoveField(
                    model_name="checklisttemplate",
                    name="version",
                ),
            ],
        ),

        # 2) Keep any ordering / Meta tweaks that 0007 was supposed to make.
        #    (Safe operations that don’t mention dropped columns.)
        migrations.AlterModelOptions(
            name="checklistitem",
            options={"ordering": ("template_id", "section", "order", "id")},
        ),
        migrations.AlterModelOptions(
            name="checklistrun",
            options={"ordering": ("-started_at",)},
        ),
        migrations.AlterModelOptions(
            name="checklisttemplate",
            options={"ordering": ("name",)},
        ),
    ]
