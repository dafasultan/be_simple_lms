# Generated by Django 5.1.4 on 2025-01-09 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms_core', '0008_coursecontent_teacher'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursecontent',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
    ]
