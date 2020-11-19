# Generated by Django 3.0.8 on 2020-08-01 19:07

import avishan.libraries.faker
import avishan.models_extensions
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0016_auto_20200726_1113'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthenticationVerification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('tried_codes', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.CreateModel(
            name='EmailKeyValueAuthentication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, help_text='Last time user sent request', null=True)),
                ('last_login', models.DateTimeField(blank=True, help_text='Last time user logged in', null=True)),
                ('last_logout', models.DateTimeField(blank=True, help_text='Last time user logged out', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('hashed_password', models.CharField(blank=True, max_length=255, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='key_value_authentications', to='avishan.Email')),
                ('user_user_group', models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, related_name='emailkeyvalueauthentication', to='avishan.UserUserGroup')),
                ('verification', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.AuthenticationVerification')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.CreateModel(
            name='EmailOtpAuthentication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, help_text='Last time user sent request', null=True)),
                ('last_login', models.DateTimeField(blank=True, help_text='Last time user logged in', null=True)),
                ('last_logout', models.DateTimeField(blank=True, help_text='Last time user logged out', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otp_authentication', to='avishan.Email')),
                ('user_user_group', models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, related_name='emailotpauthentication', to='avishan.UserUserGroup')),
                ('verification', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.AuthenticationVerification')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.CreateModel(
            name='PhoneKeyValueAuthentication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, help_text='Last time user sent request', null=True)),
                ('last_login', models.DateTimeField(blank=True, help_text='Last time user logged in', null=True)),
                ('last_logout', models.DateTimeField(blank=True, help_text='Last time user logged out', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('hashed_password', models.CharField(blank=True, max_length=255, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='key_value_authentications', to='avishan.Phone')),
                ('user_user_group', models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, related_name='phonekeyvalueauthentication', to='avishan.UserUserGroup')),
                ('verification', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.AuthenticationVerification')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.CreateModel(
            name='PhoneOtpAuthentication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, help_text='Last time user sent request', null=True)),
                ('last_login', models.DateTimeField(blank=True, help_text='Last time user logged in', null=True)),
                ('last_logout', models.DateTimeField(blank=True, help_text='Last time user logged out', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otp_authentication', to='avishan.Phone')),
                ('user_user_group', models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, related_name='phoneotpauthentication', to='avishan.UserUserGroup')),
                ('verification', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.AuthenticationVerification')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.CreateModel(
            name='VisitorKeyAuthentication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_used', models.DateTimeField(blank=True, help_text='Last time user sent request', null=True)),
                ('last_login', models.DateTimeField(blank=True, help_text='Last time user logged in', null=True)),
                ('last_logout', models.DateTimeField(blank=True, help_text='Last time user logged out', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('key', models.CharField(max_length=255)),
                ('user_user_group', models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, related_name='visitorkeyauthentication', to='avishan.UserUserGroup')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.RemoveField(
            model_name='emailverification',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='phoneotpauthenticate',
            name='key',
        ),
        migrations.RemoveField(
            model_name='phoneotpauthenticate',
            name='user_user_group',
        ),
        migrations.RemoveField(
            model_name='phonepasswordauthenticate',
            name='key',
        ),
        migrations.RemoveField(
            model_name='phonepasswordauthenticate',
            name='user_user_group',
        ),
        migrations.RemoveField(
            model_name='phoneverification',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='visitorkey',
            name='user_user_group',
        ),
        migrations.DeleteModel(
            name='EmailPasswordAuthenticate',
        ),
        migrations.DeleteModel(
            name='EmailVerification',
        ),
        migrations.DeleteModel(
            name='PhoneOTPAuthenticate',
        ),
        migrations.DeleteModel(
            name='PhonePasswordAuthenticate',
        ),
        migrations.DeleteModel(
            name='PhoneVerification',
        ),
        migrations.DeleteModel(
            name='VisitorKey',
        ),
    ]
