# Generated by Django 2.2.3 on 2019-08-14 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0003_exceptionrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessrule',
            name='crud_type',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
    ]