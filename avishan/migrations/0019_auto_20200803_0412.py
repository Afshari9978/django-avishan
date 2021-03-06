# Generated by Django 3.0.8 on 2020-08-03 04:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0018_auto_20200802_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailotpauthentication',
            name='key',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otp_authentications', to='avishan.Email'),
        ),
        migrations.AlterField(
            model_name='phoneotpauthentication',
            name='key',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otp_authentications', to='avishan.Phone'),
        ),
    ]
