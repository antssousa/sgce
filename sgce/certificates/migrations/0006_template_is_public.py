# Generated by Django 2.2.13 on 2020-08-28 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0005_auto_20200828_1230'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name='É público?'),
        ),
    ]