# Generated by Django 3.0.7 on 2020-06-25 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0013_auto_20200622_1536'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailpasswordauthenticate',
            old_name='email',
            new_name='key',
        ),
        migrations.RenameField(
            model_name='emailverification',
            old_name='email',
            new_name='identifier',
        ),
        migrations.RenameField(
            model_name='phoneotpauthenticate',
            old_name='phone',
            new_name='key',
        ),
        migrations.RenameField(
            model_name='phonepasswordauthenticate',
            old_name='phone',
            new_name='key',
        ),
        migrations.RenameField(
            model_name='phoneverification',
            old_name='phone',
            new_name='identifier',
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='verification_code',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='phoneverification',
            name='verification_code',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
