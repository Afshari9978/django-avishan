# Generated by Django 2.2.3 on 2019-09-13 18:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0009_auto_20190911_1929'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useraccessrule',
            name='access_rule',
        ),
        migrations.RemoveField(
            model_name='useraccessrule',
            name='granted_by',
        ),
        migrations.RemoveField(
            model_name='useraccessrule',
            name='user',
        ),
        migrations.DeleteModel(
            name='AccessRule',
        ),
        migrations.DeleteModel(
            name='UserAccessRule',
        ),
    ]