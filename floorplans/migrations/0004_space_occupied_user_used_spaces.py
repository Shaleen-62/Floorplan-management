# Generated by Django 5.0.6 on 2024-06-15 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floorplans', '0003_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='space',
            name='occupied',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='user',
            name='used_spaces',
            field=models.TextField(default='[]'),
        ),
    ]
