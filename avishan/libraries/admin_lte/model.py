import inspect
from typing import Tuple, Type

from django.db import models
from django.db.models import QuerySet
from django.shortcuts import redirect

from avishan import current_request
from avishan.exceptions import ErrorMessageException
from avishan.libraries.admin_lte.classes import *
from avishan.misc.translation import AvishanTranslatable
from avishan.models import AvishanModel, Image, File
from avishan.configure import get_avishan_config


class AvishanModelPanelEnabled:
    panel_view = None
    # sidebar todo: have side bar enabled class to be same az AvishanPanelWrapperView class
    sidebar_visible: bool = True
    sidebar_fa_icon: Optional[str] = 'fa-circle-o'
    sidebar_parent_view = None
    sidebar_order: int = -1

    @classmethod
    def panel_dashboard_items(cls) -> List[DashboardItem]:
        return []

    @classmethod
    def call_panel_model_function(cls: AvishanModel, model_function_name: str):
        try:
            return getattr(cls, 'panel_' + model_function_name)()
        except AttributeError:
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Model {cls.class_name()} should have a function with name "panel_{model_function_name}"'
            ))

    def call_panel_item_function(self: AvishanModel, model_function_name: str):
        try:
            return getattr(self, 'panel_' + model_function_name)()
        except AttributeError:
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Model {self.class_name()} should have a function with name "panel_{model_function_name}"'
            ))

    @classmethod
    def panel_list(cls: Union[AvishanModel, 'AvishanModelPanelEnabled']):
        from avishan.views.panel_views import AvishanPanelModelPage
        cls.panel_view: AvishanPanelModelPage
        cls.panel_view.page_header_text = cls.panel_plural_name()
        cls.panel_view.contents.append(
            Row().add_item(
                Col(12).add_item(
                    Card(
                        header=CardHeader(
                            buttons=cls.panel_list_header_buttons()
                        ),
                        body=Table(
                            heads=[TableHead(name=item[0], title=item[1]) for item in cls.panel_list_title_items()],
                            link_head_key='id',
                            link_prepend=f'/{get_avishan_config().PANEL_ROOT}/{cls.class_plural_snake_case_name()}/',
                            link_append='/detail'
                        ).add_items(
                            items=cls.panel_list_items()
                        ),
                        # footer=CardFooter().add_item(
                        #     DivComponent(element_kind='card-tools', added_classes='float-left').add_item(
                        #         Pagination(base_url='ddw', total_pages=5)
                        #     )
                        # )
                        body_added_classes='table-responsive p-0'
                    )
                )
            )
        )

    @classmethod
    def panel_create(cls: Union[AvishanModel, 'AvishanModelPanelEnabled'], edit_mode: bool = False):
        from avishan.views.panel_views import AvishanPanelModelPage
        cls.panel_view: AvishanPanelModelPage
        cls.panel_view.page_header_text = ('ویرایش' if edit_mode else 'ایجاد') + f' {cls.panel_name()}'
        created = cls.panel_view.item
        action_url = f'/{get_avishan_config().PANEL_ROOT}/{cls.class_plural_snake_case_name()}/'
        if edit_mode:
            action_url += f'{created.id}/edit'
        else:
            action_url += 'create'
        cls.panel_view.form = Form(
            action_url=action_url,
            name='create',
            button=Button(text=('ویرایش' if edit_mode else 'ایجاد')),
            disabled=True if not edit_mode and created else False
        ).add_items(cls.panel_create_form_items(item=created))

        related_forms = []
        for model, related_field_name in cls.panel_create_related_models():
            created_id = 0
            if created:
                created_id = created.id

            action_url = f'/{get_avishan_config().PANEL_ROOT}/' \
                         f'{cls.class_plural_snake_case_name()}/{created_id}/'
            if edit_mode:
                action_url += 'edit'
            else:
                action_url += 'create'
            action_url += f'?on={model.class_name()}'

            related_forms.append(Row().add_item(
                Col(6).add_item(
                    Card(
                        header=CardHeader(
                            title=model.panel_plural_name()
                        ),
                        body=Row(

                        ).add_item(
                            Col(12).add_item(
                                UnorderedList().add_items(
                                    [UnorderedListItem(
                                        data=str(item),
                                        link=f'/{get_avishan_config().PANEL_ROOT}'
                                             f'/{model.class_plural_snake_case_name()}/{item.id}'
                                    ) for item in model.objects.filter(
                                        **{related_field_name: created}
                                    )]
                                )
                            )
                        ).add_item(
                            Col(12).add_item(
                                Form(
                                    action_url=action_url,
                                    name=f'{model.class_snake_case_name()}_create',
                                    button=Button(text='افزودن'),
                                    disabled=False if created else True
                                ).add_items(model.panel_create_form_items(
                                    values_list=[(related_field_name, str(created))],
                                    disabled_list=[related_field_name]
                                ))
                            )),
                    )
                )
            ))

        if current_request['request'].method == 'POST':
            if not current_request['request'].GET.get('on'):
                data = {}
                for key, value in current_request['request'].data.items():
                    if key.startswith(cls.panel_view.form.name + "__"):
                        data[key[len(cls.panel_view.form.name) + 2:]] = value

                if edit_mode:
                    created = created.panel_edit_method(
                        **cls.panel_view.form.parse(data)
                    )
                else:
                    created = cls.panel_create_method(
                        **cls.panel_view.form.parse(data)
                    )
            else:
                related_model, related_field = cls.panel_create_related_model_find(
                    current_request['request'].GET.get('on'))
                data = {
                    related_field: created
                }
                start = related_model.class_snake_case_name() + '_create__'
                for key, value in current_request['request'].data.items():
                    if key.startswith(start):
                        data[key[len(start):]] = value
                for key, value in current_request['request'].FILES.items():
                    if key.startswith(start):
                        data[key[len(start):]] = Image.image_from_in_memory_upload(file=value)
                related_created = related_model.create(**data)

            redirect_link = f'/{get_avishan_config().PANEL_ROOT}/{cls.class_plural_snake_case_name()}/'
            if len(related_forms) == 0:
                redirect_link += f'{created.id}/detail'
            else:
                if edit_mode:
                    redirect_link += f'{created.id}/edit'
                else:
                    redirect_link += f'{created.id}/create'
            return redirect(redirect_link)
        elif current_request['request'].method == 'GET':
            cls.panel_view.contents.append(
                Row().add_item(
                    Col(large=6, extra_large=6, medium=12).add_item(
                        Card(
                            header=CardHeader(
                                buttons=created.panel_edit_form_buttons()
                                if edit_mode
                                else cls.panel_create_form_buttons(),
                                title=cls.panel_name()
                            ),
                            body=cls.panel_view.form,
                        )
                    )
                )
            )
            cls.panel_view.contents.extend(related_forms)

    def panel_detail(self: Union[AvishanModel, 'AvishanModelPanelEnabled']):
        from avishan.views.panel_views import AvishanPanelModelPage
        self.panel_view: AvishanPanelModelPage
        self.panel_view.page_header_text = f'جزئیات {self.panel_name()}'
        self.panel_view.contents.append(
            Row().add_item(
                Col(extra_large=6, large=6, medium=12).add_item(self.panel_detail_main_card())
            )
        )
        # todo: inja accardeon bezaram related haro neshoon bedim

    def panel_edit(self):
        return self.panel_create(edit_mode=True)

    def panel_delete(self):
        pass  # todo

    @classmethod
    def panel_name(cls):
        raise NotImplementedError

    @classmethod
    def panel_plural_name(cls):
        raise NotImplementedError

    @classmethod
    def panel_list_title_items(cls) -> List[Tuple[str, str]]:
        return [(
            item,
            cls.panel_translator(item)
        ) for item in cls.panel_list_title_keys()]

    @classmethod
    def panel_list_title_keys(cls) -> List[str]:
        return ['id']

    @classmethod
    def panel_list_items(cls) -> List[TableItem]:
        items = []
        for item in cls.panel_list_items_filter():
            items.append(TableItem(data_dict=item.panel_item_data_dict()))
        return items

    def panel_item_data_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def panel_list_items_filter(cls: AvishanModel) -> QuerySet:
        return cls.objects.all()

    @classmethod
    def panel_list_header_buttons(cls: Union[AvishanModel, 'AvishanModelPanelEnabled']) -> List[Button]:
        buttons = []
        if cls.panel_model_create_enable():
            buttons.append(Button(
                text='ایجاد',
                link=f'/{get_avishan_config().PANEL_ROOT}/{cls.class_plural_snake_case_name()}/create'
            ))
        return buttons

    @classmethod
    def panel_model_create_enable(cls) -> bool:
        return True

    @classmethod
    def panel_create_method(cls: Union[AvishanModel, 'AvishanModelPanelEnabled'], **kwargs):
        return cls.create(**kwargs)

    @classmethod
    def panel_create_form_buttons(cls: Union[AvishanModel, 'AvishanModelPanelEnabled']) -> List[Button]:
        return [Button(
            text='بازگشت',
            link=f'/{get_avishan_config().PANEL_ROOT}/{cls.class_plural_snake_case_name()}',
            added_classes='btn-default'
        )]

    @classmethod
    def panel_create_form_fields(cls: Union[AvishanModel, 'AvishanModelPanelEnabled']) -> List[models.Field]:
        fields = []
        for field in cls.get_fields():
            if cls.is_field_readonly(field):
                continue
            fields.append(field)
        return fields

    @classmethod
    def panel_create_form_items(cls: Union[AvishanModel, 'AvishanModelPanelEnabled'],
                                item: Union[AvishanModel, 'AvishanModelPanelEnabled'] = None,
                                values_list: List[Tuple[str, str]] = (),
                                disabled_list: List[str] = ()) -> List[FormElement]:
        items = []
        for field in cls.panel_create_form_fields():
            element_value = item.__getattribute__(field.name) if item else ""
            for name, value in values_list:
                if field.name == name:
                    element_value = value

            if isinstance(field, models.ForeignKey) and field.related_model in [Image, File]:
                form_element = FileChooseFormElement(
                    name=field.name,
                    label=cls.panel_translator(field.name),
                    disabled=True if field.name in disabled_list else False
                )
            else:
                form_element = InputFormElement(
                    name=field.name,
                    label=cls.panel_translator(field.name),
                    value=element_value,
                    disabled=True if field.name in disabled_list else False
                )
            items.append(form_element)
        return items

    @classmethod
    def panel_create_related_models(cls) -> List[Tuple[Union[Type[AvishanModel], 'AvishanModelPanelEnabled'], str]]:
        return []

    @classmethod
    def panel_create_related_model_find(cls, model_name: str) -> Optional[Tuple[Type[AvishanModel], str]]:
        for model, related_field in cls.panel_create_related_models():
            if model.class_name() == model_name:
                return model, related_field
        return None

    @classmethod
    def panel_translator(cls, text: str) -> str:
        try:
            return cls.panel_translator_dict()[text.lower()]
        except KeyError:
            return text

    @classmethod
    def panel_translator_dict(cls) -> dict:
        return {**{
            'id': 'شناسه',
            'title': 'عنوان',
            'order': 'ترتیب',
            'image': 'عکس',
            'text': 'متن',
            'parking': 'پارکینگ'
        }, **get_avishan_config().PANEL_TRANSLATION_DICT}

    def panel_detail_buttons(self: Union[AvishanModel, 'AvishanModelPanelEnabled']) -> List[Button]:
        buttons = []
        if self.panel_edit_model_enable():
            buttons.append(
                Button(
                    text='ویرایش',
                    link=f'/{get_avishan_config().PANEL_ROOT}/{self.class_plural_snake_case_name()}/{self.id}/edit',
                    added_classes='btn-success'
                )
            )
        buttons.append(Button(
            text='بازگشت',
            link=f'/{get_avishan_config().PANEL_ROOT}/{self.class_plural_snake_case_name()}',
            added_classes='btn-default'
        ))
        return buttons

    def panel_detail_items(self):
        items = []
        for name in self.panel_detail_keys():
            if inspect.ismethod(self.__getattribute__(name)):
                value = self.__getattribute__(name)()
            else:
                value = self.__getattribute__(name)
            items.append((self.panel_translator(name), value))
        return items

    @classmethod
    def panel_detail_related_models(cls) -> List[Tuple[Union[Type[AvishanModel], 'AvishanModelPanelEnabled'], str]]:
        return []

    @classmethod
    def panel_detail_keys(cls: Union[AvishanModel, 'AvishanModelPanelEnabled']):
        return [field.name for field in cls.get_fields()]

    def panel_detail_main_card(self) -> Card:
        card = Card(
            header=CardHeader(
                buttons=self.panel_detail_buttons()
            )
        )
        if len(self.panel_detail_main_card_items()) == 1:
            card.body = self.panel_detail_main_card_items()[0]
        else:
            for tab in self.panel_detail_main_card_items():
                tab: CardTab
                card.add_tab(tab)
        return card

    def panel_detail_main_card_items(self) -> Union[List[DivComponent]]:
        return [DataList().add_items(self.panel_detail_items())]

    @classmethod
    def panel_edit_model_enable(cls) -> bool:
        return True

    def panel_edit_method(self: Union[AvishanModel, 'AvishanModelPanelEnabled'], **kwargs):
        return self.update(**kwargs)

    def panel_edit_form_buttons(self: Union[AvishanModel, 'AvishanModelPanelEnabled']) -> List[Button]:
        return [Button(
            text='بازگشت',
            link=f'/{get_avishan_config().PANEL_ROOT}/{self.class_plural_snake_case_name()}/{self.id}/detail',
            added_classes='btn-default'
        )]
