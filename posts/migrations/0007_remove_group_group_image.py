# Generated by Django 2.2.6 on 2021-03-24 16:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_group_group_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='group_image',
        ),
    ]
