# Generated by Django 3.0.8 on 2020-08-03 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0019_auto_20200803_0412'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailkeyvalueauthentication',
            name='is_active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='emailotpauthentication',
            name='is_active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='phonekeyvalueauthentication',
            name='is_active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='phoneotpauthentication',
            name='is_active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='visitorkeyauthentication',
            name='is_active',
            field=models.BooleanField(blank=True, default=True),
        ),
    ]
