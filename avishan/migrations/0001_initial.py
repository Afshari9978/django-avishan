# Generated by Django 2.2.6 on 2019-12-15 21:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=255, unique=True)),
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestTrack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField(blank=True, null=True)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('method', models.CharField(blank=True, max_length=255, null=True)),
                ('json_unsafe', models.BooleanField(blank=True, null=True)),
                ('is_api', models.BooleanField(blank=True, null=True)),
                ('add_token', models.BooleanField(blank=True, null=True)),
                ('request_data', models.TextField(blank=True, null=True)),
                ('request_headers', models.TextField(blank=True, null=True)),
                ('response_data', models.TextField(blank=True, null=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('total_execution_milliseconds', models.BigIntegerField(blank=True, null=True)),
                ('view_execution_milliseconds', models.BigIntegerField(blank=True, null=True)),
                ('authentication_type_class_title', models.CharField(blank=True, max_length=255, null=True)),
                ('authentication_type_object_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('token_valid_seconds', models.BigIntegerField(blank=True, default=1800)),
                ('authenticate_with_email_password', models.BooleanField(default=False)),
                ('authenticate_with_phone_password', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserUserGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('base_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_user_groups', to='avishan.BaseUser')),
                ('user_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_user_groups', to='avishan.UserGroup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestTrackMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=255)),
                ('title', models.TextField(blank=True, null=True)),
                ('body', models.TextField(blank=True, null=True)),
                ('code', models.CharField(blank=True, max_length=255, null=True)),
                ('request_track', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='avishan.RequestTrack')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestTrackException',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_title', models.CharField(blank=True, max_length=255, null=True)),
                ('args', models.TextField(blank=True, null=True)),
                ('traceback', models.TextField(blank=True, null=True)),
                ('request_track', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='exception', to='avishan.RequestTrack')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='requesttrack',
            name='user_user_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.UserUserGroup'),
        ),
        migrations.CreateModel(
            name='PhonePasswordAuthenticate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, default=None, null=True)),
                ('last_login', models.DateTimeField(blank=True, default=None, null=True)),
                ('last_logout', models.DateTimeField(blank=True, default=None, null=True)),
                ('phone', models.CharField(max_length=255)),
                ('hashed_password', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('user_user_group', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='avishan.UserUserGroup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(blank=True, null=True, upload_to='')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('base_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.BaseUser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, upload_to='')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('base_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.BaseUser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailVerification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verification_code', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('verification_date', models.DateTimeField(auto_now_add=True)),
                ('tried_codes', models.TextField(blank=True, default='')),
                ('email', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='verification', to='avishan.Email')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailPasswordAuthenticate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, default=None, null=True)),
                ('last_login', models.DateTimeField(blank=True, default=None, null=True)),
                ('last_logout', models.DateTimeField(blank=True, default=None, null=True)),
                ('hashed_password', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_authenticates', to='avishan.Email')),
                ('user_user_group', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='avishan.UserUserGroup')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
