# Generated by Django 3.0.8 on 2020-08-02 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0017_auto_20200801_1907'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='email',
            name='date_verified',
        ),
        migrations.RemoveField(
            model_name='emailkeyvalueauthentication',
            name='is_verified',
        ),
        migrations.RemoveField(
            model_name='phone',
            name='date_verified',
        ),
        migrations.RemoveField(
            model_name='phonekeyvalueauthentication',
            name='is_verified',
        ),
        migrations.AddField(
            model_name='emailkeyvalueauthentication',
            name='date_verified',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='emailotpauthentication',
            name='date_verified',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='phonekeyvalueauthentication',
            name='date_verified',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='phoneotpauthentication',
            name='date_verified',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='authenticationverification',
            name='tried_codes',
            field=models.TextField(blank=True, default=''),
        ),
    ]