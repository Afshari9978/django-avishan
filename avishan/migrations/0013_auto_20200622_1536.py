# Generated by Django 3.0.7 on 2020-06-22 15:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0012_delete_requesttrackexecinfo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='email',
            old_name='address',
            new_name='key',
        ),
        migrations.RenameField(
            model_name='phone',
            old_name='number',
            new_name='key',
        ),
    ]
