from typing import Optional, List, Type, Union

from django.shortcuts import redirect

from avishan import current_request
from avishan.configure import get_avishan_config
from avishan.exceptions import AvishanException, AuthException, ErrorMessageException
from avishan.libraries.admin_lte.classes import *
from avishan.libraries.admin_lte.model import AvishanModelPanelEnabled
from avishan.misc.translation import AvishanTranslatable
from avishan.models import AvishanModel, KeyValueAuthentication, EmailPasswordAuthenticate, PhonePasswordAuthenticate, \
    OtpAuthentication, AuthenticationType, UserGroup
from avishan.utils import all_subclasses
from avishan.views.class_based import AvishanTemplateView


class AvishanPanelWrapperView(AvishanTemplateView):
    template_file_address: str = 'avishan/panel/pages/panel_page.html'
    template_url: str = None

    # sidebar
    sidebar_visible: bool = False
    sidebar_title: Optional[str] = 'Untitled'
    sidebar_fa_icon: Optional[str] = 'fa-circle-o'
    sidebar_parent_view: Optional['AvishanPanelWrapperView'] = None
    sidebar_order: int = -1

    def dispatch(self, request, *args, **kwargs):
        self.parse_request_post_to_data()
        try:
            result = self._dispatch(request, *args, **kwargs)
            if result is None:
                return self.render()
            return result
        except AvishanException as e:
            if isinstance(e, AuthException) and e.error_kind in AuthException.get_login_required_errors():
                return redirect(to=AvishanPanelLoginPage.template_url)
        except Exception as e:
            AvishanException(wrap_exception=e)
        return redirect(to=AvishanPanelErrorPage.template_url + f'?from={self.template_url}', felan=self.template_url)

    def _dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render()


class AvishanPanelLoginPage(AvishanPanelWrapperView):
    template_file_address = 'avishan/panel/pages/login_page.html'
    template_url = f'/{get_avishan_config().PANEL_ROOT}/login'
    login_class: Type[AuthenticationType] = None
    authenticate = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_class: Type = AvishanModel.get_model_with_class_name(get_avishan_config().PANEL_LOGIN_CLASS_NAME)
        self.form = Form(
            action_url=self.template_url,
            method='post',
            button=Button(text='ورود'),
            items_margin=Margin(bottom=2),
            name='sign_in'
        )
        if issubclass(self.login_class, KeyValueAuthentication):
            if issubclass(self.login_class, EmailPasswordAuthenticate):
                self.form.add_item(IconAddedInputFormElement(
                    name='key',
                    input_type='email',
                    fa_icon='fa-envelope',
                    label='ایمیل'
                ))
            elif issubclass(self.login_class, PhonePasswordAuthenticate):
                self.form.add_item(IconAddedInputFormElement(
                    name='key',
                    input_type='tel',
                    fa_icon='fa-phone-square',
                    label='شماره همراه'
                ))
            else:
                raise NotImplementedError

            self.context['login_type'] = 'key_value'
            self.form.add_item(IconAddedInputFormElement(
                name='value',
                input_type='password',
                fa_icon='fa-lock',
                label='رمز عبور'
            ))
        elif issubclass(self.login_class, OtpAuthentication):
            self.context['login_type'] = 'otp'
            raise NotImplementedError  # todo
        else:
            raise NotImplementedError

    def post(self, request, *args, **kwargs):

        if issubclass(self.login_class, OtpAuthentication):
            raise NotImplementedError
        elif issubclass(self.login_class, KeyValueAuthentication):
            self.login_class.login(
                key=self.request.data['sign_in__key'],
                password=self.request.data['sign_in__value'],
                user_group=UserGroup.get(title=get_avishan_config().PANEL_LOGIN_USER_GROUP_TITLE)
            )
        return redirect(AvishanPanelPage.template_url)


class AvishanPanelLogoutPage(AvishanPanelWrapperView):
    template_url = f'/{get_avishan_config().PANEL_ROOT}/logout'

    def get(self, request, *args, **kwargs):
        self.current_request['add_token'] = False
        return redirect(AvishanPanelLoginPage.template_url)


class AvishanPanelErrorPage(AvishanPanelWrapperView):
    template_file_address = 'avishan/panel/pages/error_page.html'
    template_url = f'/{get_avishan_config().PANEL_ROOT}/error'
    authenticate = False

    def get(self, request, *args, **kwargs):
        self.redirected_from = self.request.GET.get('from', None)
        if self.redirected_from == self.template_url:
            self.redirected_from = get_avishan_config().PANEL_ROOT
        return self.render()


class AvishanPanelPage(AvishanPanelWrapperView):
    template_url = f'/{get_avishan_config().PANEL_ROOT}'
    page_header_text: str = ''
    track_it = True
    contents: List[DivComponent] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clean_class()

        self.sidebar = Sidebar().add_item(
            SidebarItem(
                text='داشبورد',
                link=f'/{get_avishan_config().PANEL_ROOT}',
                icon='fa-dashboard'
            )
        )
        for sub_class in sorted(all_subclasses(AvishanModelPanelEnabled), key=lambda x: x.sidebar_order):
            if sub_class._meta.abstract or not sub_class.sidebar_visible:
                continue
            sub_class: Union[AvishanModel, AvishanModelPanelEnabled]
            self.sidebar.add_item(
                SidebarItem(
                    text=sub_class.panel_plural_name(),
                    link=f'/{get_avishan_config().PANEL_ROOT}/{sub_class.class_plural_snake_case_name()}',
                    icon=sub_class.sidebar_fa_icon
                )
            )

        self.navbar = Navbar(background_color=Color('white'))
        self.navbar.navbar_items.append(NavbarItem(link=AvishanPanelLogoutPage.template_url, icon='fa-sign-out'))

    def clean_class(self):
        # todo can we do something to prevent this shit? maybe not static values
        self.page_header_text = ""
        self.contents = []

    def get(self, request, *args, **kwargs):
        pass


class AvishanPanelDashboardPage(AvishanPanelPage):
    template_url = f'/{get_avishan_config().PANEL_ROOT}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dashboard_items: List[DashboardItem] = []
        self.page_header_text = 'داشبورد'
        for model in all_subclasses(AvishanModelPanelEnabled):
            model: AvishanModelPanelEnabled
            self.dashboard_items.extend(model.panel_dashboard_items())

    def rows(self) -> List[Row]:
        rows = {}
        created = []
        for item in sorted(self.dashboard_items, key=lambda x: x.row):
            if item.row not in rows.keys():
                rows[item.row] = []
            rows[item.row].append(item)
        for row_key in sorted(rows.keys()):
            row = Row()
            for item in sorted(rows[row_key], key=lambda x: x.order):
                item: DashboardItem
                row.add_item(item.col.add_item(
                    item.item
                ))
            created.append(row)
        return created

    def get(self, request, *args, **kwargs):
        self.contents.extend(self.rows())
        return super().get(request, *args, **kwargs)


class AvishanPanelModelPage(AvishanPanelPage):
    model: Optional[Type[Union[AvishanModel, AvishanModelPanelEnabled]]] = None
    item: Optional[Union[AvishanModel, AvishanModelPanelEnabled]] = None
    model_function: Optional[str] = None
    item_id: Optional[int] = None
    item_function: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clean_class()
        self.populate_from_url()

        if self.model is None:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Model not found'
            ))
        if not issubclass(self.model, AvishanModelPanelEnabled):
            raise ErrorMessageException(AvishanTranslatable(
                EN='Model not inherited from "AvishanPanelEnabled" class'
            ))
        self.model.panel_view = self

    def _dispatch(self, request, *args, **kwargs):
        if self.model_function:
            return self.model.call_panel_model_function(self.model_function)
        if self.item_id:
            try:
                self.item = self.model.get(id=self.item_id)
            except self.model.DoesNotExist:
                ErrorMessageException(AvishanTranslatable(
                    EN=f'Item not found with id={self.item_id}'
                ))

            if self.item_function:
                return self.item.call_panel_item_function(self.item_function)
            return redirect(self.request.path + "/detail", permanent=True)
        return self.model.call_panel_model_function('list')

    @property
    def template_url(self) -> str:
        return f'/{get_avishan_config().PANEL_ROOT}/{self.model.class_plural_snake_case_name()}'

    def populate_from_url(self):
        url = current_request['request'].path[len(get_avishan_config().PANEL_ROOT) + 2:]
        url = url.split("/")

        self.model = AvishanModel.get_model_by_plural_snake_case_name(url[0])
        if len(url) > 1:
            try:
                self.item_id = int(url[1])
                if len(url) > 2:
                    self.item_function = url[2]
            except ValueError:
                self.model_function = url[1]
        # todo add more conditions here

    def clean_class(self):
        super().clean_class()
        self.model = None
        self.item = None
        self.model_function = None
        self.item_id = None
        self.item_function = None


# todo font awesome 5

class AvishanPanelTestPage(AvishanTemplateView):
    authenticate = False
    template_file_address = 'avishan/panel/test_page.html'

    def get(self, request, *args, **kwargs):
        return self.render()
