# Generated by Django 2.0.6 on 2018-06-27 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geocontext', '0005_contextgroup_context_service_registries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contextgroupservices',
            name='order',
            field=models.IntegerField(blank=True, default=0, verbose_name='Order'),
        ),
    ]
