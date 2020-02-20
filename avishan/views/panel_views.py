from typing import Type, Optional

from django.contrib import messages
from django.shortcuts import redirect

from avishan.configure import get_avishan_config
from avishan.exceptions import ErrorMessageException, AuthException
from avishan.libraries.admin_lte.classes import DataList
from avishan.misc.translation import AvishanTranslatable
from avishan.models import AvishanModel, OtpAuthentication, KeyValueAuthentication, UserGroup, Phone
from avishan.views.class_based import AvishanTemplateView


class AvishanPanelView(AvishanTemplateView):
    template_address = 'avishan/panel/panel_page.html'
    template_url = '/panel'
    show_on_sidebar = False
    title: str = None
    icon: str = 'fa-circle-o'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context['CONFIG'] = get_avishan_config()
        self.context['sidebar_items'] = [
            {
                'title': 'داشبورد',
                'icon': 'fa-dashboard',
                'link': ''
            }
        ]
        for item in AvishanModel.all_subclasses(AvishanPanelView):
            item: AvishanPanelView
            if item.show_on_sidebar:
                self.context['sidebar_items'].append({
                    'title': item.title,
                    'icon': item.icon if item.icon is not None else 'fa-circle',
                    'link': item.template_url
                })
        self.template_url = self.request.path
        self.context['page_header'] = "حذف شود"

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except AuthException as e:
            return redirect(AvishanPanelLoginView.template_url, permanent=True)

    def get(self, request, *args, **kwargs):
        return self.render()

    def render(self):
        from django.shortcuts import render as django_render
        return django_render(self.request, self.template_address, self.context)


class AvishanPanelLoginView(AvishanPanelView):
    authenticate = False
    template_address = 'avishan/panel/pages/login.html'
    template_url = '/panel/login'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.login_class = AvishanModel.get_model_with_class_name(
            get_avishan_config().PANEL_LOGIN_CLASS)
        self.user_group = UserGroup.get(
            title=get_avishan_config().PANEL_LOGIN_USER_GROUP_TITLE
        )
        self.context['login_key_placeholder'] = self.login_class.key_field().name

    def get(self, request, *args, **kwargs):
        if get_avishan_config().PANEL_OTP_LOGIN:
            self.login_class: OtpAuthentication
        else:
            self.login_class: KeyValueAuthentication

        self.context['otp_key'] = ""
        return self.render()

    def post(self, request, *args, **kwargs):
        if get_avishan_config().PANEL_OTP_LOGIN:
            self.login_class: OtpAuthentication
        else:
            self.login_class: KeyValueAuthentication

        if 'otp_send' in request.data.keys():
            # todo async it
            # todo age por bood shomare, focus on code
            for model in get_avishan_config().get_otp_users():
                model: AvishanModel
                try:
                    model.get(phone=Phone.get_or_create_phone(request.data['otp_key']))
                except model.DoesNotExist:
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
            return self.render()
        else:
            self.login_class.complete_challenge(
                key=request.data['otp_key'],
                code=request.data['otp_code'],
                user_group=self.user_group
            )
            return redirect(AvishanPanelView.template_url)


class AvishanPanelListView(AvishanPanelView):
    template_address = 'avishan/panel/pages/list_page.html'
    item_id = None
    view_action = None
    item_action = None
    head_url = None
    data_list = DataList()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.head_url = "/" + self.request.path.split("/")[1] + "/" + self.request.path.split("/")[2]
        self.context['head_url'] = self.head_url

    def dispatch(self, request, *args, **kwargs):
        if 'item_id' in kwargs.keys():
            self.item_id = kwargs['item_id']
        if 'view_action' in kwargs.keys():
            self.view_action = kwargs['view_action']
        if 'item_action' in kwargs.keys():
            self.item_action = kwargs['item_action']

        if self.view_action == 'create':
            return self.create(request, *args, **kwargs)
        if self.item_id is not None:
            if self.item_action == 'delete':
                return self.delete(request, *args, **kwargs)
            if self.item_action == 'edit':
                return self.edit(request, *args, **kwargs)
            return self.detail(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        print('list')
        self.context['data_list'] = self.data_list
        return self.render()

    def create(self, request, *args, **kwargs):
        print('create')
        return self.render()

    def edit(self, request, *args, **kwargs):
        print('edit')
        return self.render()

    def delete(self, request, *args, **kwargs):
        print('delete')
        return self.render()

    def detail(self, request, *args, **kwargs):
        print('detail')
        return self.render()
