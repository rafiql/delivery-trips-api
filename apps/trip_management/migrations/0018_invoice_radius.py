# Generated by Django 2.2.3 on 2022-01-05 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trip_management', '0017_auto_20211226_0716'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='radius',
            field=models.PositiveSmallIntegerField(default=100),
        ),
    ]
