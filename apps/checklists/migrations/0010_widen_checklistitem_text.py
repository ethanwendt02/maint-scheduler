from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0009_remove_checklistrun_created_at_checklistitem_section_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklistitem',
            name='text',
            field=models.TextField(),
        ),
    ]
