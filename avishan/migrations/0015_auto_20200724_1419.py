# Generated by Django 3.0.8 on 2020-07-24 14:19

import avishan.libraries.faker
import avishan.models_extensions
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('avishan', '0014_auto_20200625_1319'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('alpha_2_code', models.CharField(max_length=255)),
                ('alpha_3_code', models.CharField(max_length=255)),
                ('region', models.CharField(max_length=255)),
                ('native_name', models.CharField(blank=True, max_length=255, null=True)),
                ('numeric_code', models.CharField(max_length=255, unique=True)),
                ('flag_url', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, avishan.libraries.faker.AvishanFaker, avishan.models_extensions.AvishanModelDjangoAdminExtension, avishan.models_extensions.AvishanModelModelDetailsExtension, avishan.models_extensions.AvishanModelFilterExtension),
        ),
        migrations.AlterField(
            model_name='baseuser',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, help_text='Date user joined system'),
        ),
        migrations.AlterField(
            model_name='baseuser',
            name='is_active',
            field=models.BooleanField(blank=True, default=True, help_text='Checks if user can use system'),
        ),
        migrations.AlterField(
            model_name='baseuser',
            name='language',
            field=models.CharField(default='EN', help_text='Language for user, using 2 words ISO standard: EN, FA, AR', max_length=255),
        ),
        migrations.AlterField(
            model_name='email',
            name='date_verified',
            field=models.DateTimeField(blank=True, default=None, help_text='Last date identifier accepted', null=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='key',
            field=models.CharField(help_text='Unique value of target data', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='emailpasswordauthenticate',
            name='hashed_password',
            field=models.CharField(blank=True, default=None, help_text='Hashed password', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='emailpasswordauthenticate',
            name='key',
            field=models.ForeignKey(help_text='Related Email object', on_delete=django.db.models.deletion.CASCADE, related_name='password_authenticates', to='avishan.Email'),
        ),
        migrations.AlterField(
            model_name='emailpasswordauthenticate',
            name='last_login',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged in', null=True),
        ),
        migrations.AlterField(
            model_name='emailpasswordauthenticate',
            name='last_logout',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged out', null=True),
        ),
        migrations.AlterField(
            model_name='emailpasswordauthenticate',
            name='last_used',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user sent request', null=True),
        ),
        migrations.AlterField(
            model_name='emailpasswordauthenticate',
            name='user_user_group',
            field=models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, to='avishan.UserUserGroup'),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='identifier',
            field=models.OneToOneField(help_text='Related Email object', on_delete=django.db.models.deletion.CASCADE, related_name='verification', to='avishan.Email'),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='tried_codes',
            field=models.TextField(blank=True, default='', help_text='Incorrect codes user tried'),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='verification_code',
            field=models.CharField(help_text='Code sent to user', max_length=255),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='verification_date',
            field=models.DateTimeField(auto_now_add=True, help_text='Date code sent to user'),
        ),
        migrations.AlterField(
            model_name='file',
            name='base_user',
            field=models.ForeignKey(blank=True, help_text='Uploaded by', null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.BaseUser'),
        ),
        migrations.AlterField(
            model_name='file',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, help_text='Date uploaded'),
        ),
        migrations.AlterField(
            model_name='file',
            name='file',
            field=models.FileField(blank=True, help_text='File url', null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='image',
            name='base_user',
            field=models.ForeignKey(blank=True, help_text='Uploaded by', null=True, on_delete=django.db.models.deletion.SET_NULL, to='avishan.BaseUser'),
        ),
        migrations.AlterField(
            model_name='image',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, help_text='Date uploaded'),
        ),
        migrations.AlterField(
            model_name='image',
            name='file',
            field=models.ImageField(blank=True, help_text='Image url', null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='phone',
            name='date_verified',
            field=models.DateTimeField(blank=True, default=None, help_text='Last date identifier accepted', null=True),
        ),
        migrations.AlterField(
            model_name='phone',
            name='key',
            field=models.CharField(help_text='Unique value of target data', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='code',
            field=models.CharField(blank=True, help_text='Code sent to user', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='date_sent',
            field=models.DateTimeField(blank=True, default=None, help_text='Date code sent to user', null=True),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='key',
            field=models.ForeignKey(help_text='Related Phone object', on_delete=django.db.models.deletion.CASCADE, related_name='otp_authenticates', to='avishan.Phone'),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='last_login',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged in', null=True),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='last_logout',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged out', null=True),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='last_used',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user sent request', null=True),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='tried_codes',
            field=models.TextField(blank=True, default='', help_text='Incorrect user tried codes'),
        ),
        migrations.AlterField(
            model_name='phoneotpauthenticate',
            name='user_user_group',
            field=models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, to='avishan.UserUserGroup'),
        ),
        migrations.AlterField(
            model_name='phonepasswordauthenticate',
            name='hashed_password',
            field=models.CharField(blank=True, default=None, help_text='Hashed password', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='phonepasswordauthenticate',
            name='key',
            field=models.ForeignKey(help_text='Related Phone object', on_delete=django.db.models.deletion.CASCADE, related_name='password_authenticates', to='avishan.Phone'),
        ),
        migrations.AlterField(
            model_name='phonepasswordauthenticate',
            name='last_login',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged in', null=True),
        ),
        migrations.AlterField(
            model_name='phonepasswordauthenticate',
            name='last_logout',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged out', null=True),
        ),
        migrations.AlterField(
            model_name='phonepasswordauthenticate',
            name='last_used',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user sent request', null=True),
        ),
        migrations.AlterField(
            model_name='phonepasswordauthenticate',
            name='user_user_group',
            field=models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, to='avishan.UserUserGroup'),
        ),
        migrations.AlterField(
            model_name='phoneverification',
            name='identifier',
            field=models.OneToOneField(help_text='Related Phone object', on_delete=django.db.models.deletion.CASCADE, related_name='verification', to='avishan.Phone'),
        ),
        migrations.AlterField(
            model_name='phoneverification',
            name='tried_codes',
            field=models.TextField(blank=True, default='', help_text='Incorrect codes user tried'),
        ),
        migrations.AlterField(
            model_name='phoneverification',
            name='verification_code',
            field=models.CharField(help_text='Code sent to user', max_length=255),
        ),
        migrations.AlterField(
            model_name='phoneverification',
            name='verification_date',
            field=models.DateTimeField(auto_now_add=True, help_text='Date code sent to user'),
        ),
        migrations.AlterField(
            model_name='usergroup',
            name='title',
            field=models.CharField(help_text='Project specific groups, like "driver", "customer"', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='usergroup',
            name='token_valid_seconds',
            field=models.BigIntegerField(blank=True, default=1800, help_text='Token valid seconds'),
        ),
        migrations.AlterField(
            model_name='userusergroup',
            name='base_user',
            field=models.ForeignKey(help_text='BaseUser object side', on_delete=django.db.models.deletion.CASCADE, related_name='user_user_groups', to='avishan.BaseUser'),
        ),
        migrations.AlterField(
            model_name='userusergroup',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, help_text='Date BaseUser added to this UserGroup'),
        ),
        migrations.AlterField(
            model_name='userusergroup',
            name='is_active',
            field=models.BooleanField(blank=True, default=True, help_text='Is BaseUser active with this UserGroup'),
        ),
        migrations.AlterField(
            model_name='userusergroup',
            name='user_group',
            field=models.ForeignKey(help_text='UserGroup object side', on_delete=django.db.models.deletion.CASCADE, related_name='user_user_groups', to='avishan.UserGroup'),
        ),
        migrations.AlterField(
            model_name='visitorkey',
            name='key',
            field=models.CharField(help_text='Random generated key', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='visitorkey',
            name='last_login',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged in', null=True),
        ),
        migrations.AlterField(
            model_name='visitorkey',
            name='last_logout',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user logged out', null=True),
        ),
        migrations.AlterField(
            model_name='visitorkey',
            name='last_used',
            field=models.DateTimeField(blank=True, default=None, help_text='Last time user sent request', null=True),
        ),
        migrations.AlterField(
            model_name='visitorkey',
            name='user_user_group',
            field=models.OneToOneField(help_text='Target UserUserGroup', on_delete=django.db.models.deletion.CASCADE, to='avishan.UserUserGroup'),
        ),
    ]
