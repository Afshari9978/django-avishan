from typing import Type, Optional

from django.contrib import messages
from django.shortcuts import render, redirect

from avishan.configure import get_avishan_config
from avishan.exceptions import ErrorMessageException
from avishan.misc.translation import AvishanTranslatable
from avishan.models import AvishanModel, AuthenticationType, OtpAuthentication, KeyValueAuthentication, UserGroup, Phone
from avishan.views.class_based import AvishanTemplateView


class AvishanPanelView(AvishanTemplateView):
    template_address = 'avishan/panel/panel_page.html'
    template_url = '/panel'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context['CONFIG'] = get_avishan_config()

    def get(self, request, *args, **kwargs):
        return render(self.request, self.template_address, self.context)


class AvishanPanelLoginView(AvishanPanelView):
    authenticate = False
    template_address = 'avishan/panel/login.html'
    template_url = '/panel/login'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.login_class = AvishanModel.get_model_with_class_name(
            get_avishan_config().PANEL_LOGIN_CLASS)
        self.user_group = UserGroup.get(
            title=get_avishan_config().PANEL_LOGIN_USER_GROUP_TITLE
        )

    def get(self, request, *args, **kwargs):
        if get_avishan_config().PANEL_OTP_LOGIN:
            self.login_class: OtpAuthentication
        else:
            self.login_class: KeyValueAuthentication

        self.context['login_key_placeholder'] = self.login_class.key_field().name
        return render(self.request, self.template_address, self.context)

    def post(self, request, *args, **kwargs):
        if get_avishan_config().PANEL_OTP_LOGIN:
            self.login_class: OtpAuthentication
        else:
            self.login_class: KeyValueAuthentication

        if 'otp_send' in request.data.keys():
            # todo async it
            # todo age por bood shomare, focus on code
            try:
                Employee.get(phone=Phone.get_or_create_phone(request.data['otp_key']))
            except Employee.DoesNotExist:
                raise ErrorMessageException(
                    AvishanTranslatable(
                        EN='User not found',
                        FA='کاربری با این شماره پیدا نشد'
                    )
                )
            self.login_class.start_challenge(
                key=request.data['otp_key'],
                user_group=self.user_group
            )
            messages.success(self.request, AvishanTranslatable(
                EN=f'Otp code sent successfully',
                FA=f'کد ورود با موفقیت ارسال شد',
            ))

            # todo do something when code sent
            self.context['otp_key'] = self.request.data['otp_key']
            return render(self.request, self.template_address, self.context)
        else:
            self.login_class.complete_challenge(
                key=request.data['otp_key'],
                code=request.data['otp_code'],
                user_group=self.user_group
            )
            return redirect(AvishanPanelView.template_url, permanent=True)
