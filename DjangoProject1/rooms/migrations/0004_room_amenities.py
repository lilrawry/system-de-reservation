# Generated by Django 5.2 on 2025-04-07 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0003_auto_20250407_0948'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='amenities',
            field=models.JSONField(default=list, verbose_name='Équipements'),
        ),
    ]
