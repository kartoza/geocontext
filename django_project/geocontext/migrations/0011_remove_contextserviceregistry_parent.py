# Generated by Django 2.0.6 on 2018-06-29 09:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geocontext', '0010_auto_20180627_1411'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contextserviceregistry',
            name='parent',
        ),
    ]
