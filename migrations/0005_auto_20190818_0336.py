# Generated by Django 2.2.3 on 2019-08-18 03:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0004_accessrule_crud_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exceptionrecord',
            name='http_method',
        ),
        migrations.RemoveField(
            model_name='exceptionrecord',
            name='url',
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='datetime',
            field=models.DateTimeField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='request_data',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='request_method',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='request_url',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='response',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='status_code',
            field=models.IntegerField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='traceback',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.User'),
        ),
        migrations.AddField(
            model_name='exceptionrecord',
            name='user_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.UserGroup'),
        ),
    ]
