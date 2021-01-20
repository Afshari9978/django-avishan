from typing import Optional, List, Union, Type

import django_filters
import stringcase
from crum import get_current_request
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.db.models import NOT_PROVIDED, QuerySet, Field

from avishan.descriptor import FunctionAttribute, DjangoFieldAttribute, ResponseBodyDocumentation, Attribute, \
    RequestBodyDocumentation, DataModel, Function
from avishan.misc import status

import ast


class AvishanModelDjangoAdminExtension:
    django_admin_date_hierarchy: Optional[str] = None
    django_admin_list_display: List[models.Field] = []
    django_admin_list_filter: List[models.Field] = []
    django_admin_list_max_show_all: int = 300
    django_admin_list_per_page: int = 100
    django_admin_raw_id_fields: List[models.Field] = []
    django_admin_readonly_fields: List[models.Field] = []
    django_admin_search_fields: List[models.Field] = []


class AvishanModelModelDetailsExtension:
    UNCHANGED = '__UNCHANGED__'

    @classmethod
    def class_name(cls) -> str:
        return cls.__name__

    @classmethod
    def class_plural_name(cls) -> str:
        return cls.class_name() + "s"

    @classmethod
    def class_snake_case_name(cls) -> str:
        return stringcase.snakecase(cls.class_name())

    @classmethod
    def class_plural_snake_case_name(cls) -> str:
        return stringcase.snakecase(cls.class_plural_name())

    @classmethod
    def app_name(cls) -> str:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return cls._meta.app_label

    @staticmethod
    def get_non_abstract_models(app_name: str = None) -> List[type]:
        from avishan.models import AvishanModel
        return [x for x in AvishanModel.get_models(app_name) if x._meta.abstract is False]

    @staticmethod
    def get_models(app_name: str = None) -> list:
        from avishan.models import AvishanModel

        def get_sub_classes(parent):
            subs = [parent]
            for child in parent.__subclasses__():
                subs += get_sub_classes(child)
            return subs

        total = []
        if not app_name:
            for model in AvishanModel.__subclasses__():
                total += get_sub_classes(model)
            return list(set(total))

        return [x for x in AvishanModel.get_models() if x._meta.app_label == app_name]

    @staticmethod
    def get_model_with_class_name(class_name: str) -> Optional[type]:
        from avishan.models import AvishanModel
        for item in AvishanModel.get_models():
            if item.class_name() == class_name:
                return item
        return None

    @staticmethod
    def get_model_by_plural_snake_case_name(name: str) -> Optional[type]:
        from avishan.models import AvishanModel
        for model in AvishanModel.get_non_abstract_models():
            model: AvishanModel
            if model.class_plural_snake_case_name() == name:
                return model
        return None

    @staticmethod
    def get_model_by_snake_case_name(name: str) -> Optional[type]:
        from avishan.models import AvishanModel
        for model in AvishanModel.get_non_abstract_models():
            model: AvishanModel
            if model.class_snake_case_name() == name:
                return model
        return None

    @staticmethod
    def get_app_names() -> List[str]:
        from django.apps import apps
        from avishan.configure import get_avishan_config
        return [key.name for key in apps.get_app_configs() if
                key.name in get_avishan_config().MONITORED_APPS_NAMES]

    @classmethod
    def get_fields(cls) -> List[models.Field]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return list(cls._meta.fields)

    @classmethod
    def get_full_fields(cls) -> List[models.Field]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return list(cls._meta.fields + cls._meta.many_to_many)

    @classmethod
    def get_field(cls, field_name: str) -> models.Field:
        from avishan.misc.translation import AvishanTranslatable

        for item in cls.get_full_fields():
            if item.name == field_name:
                return item
        raise ValueError(AvishanTranslatable(
            EN=f'field {field_name} not found in model {cls.class_name()}'
        ))

    @classmethod
    def is_field_identifier_for_model(cls, field: models.Field) -> bool:
        """
        Checks if field is enough for finding an object from db.
        :param field: for example for 'id' or other unique fields, it will be True
        :return:
        """
        return field.primary_key or field.unique

    @staticmethod
    def is_field_readonly(field: models.Field) -> bool:
        """
        Checks if field is read-only type and must not entered by user
        :param field: for example auto create date-times
        :return:
        """
        if (isinstance(field, models.DateField) or isinstance(field, models.DateTimeField) or
            isinstance(field, models.TimeField)) and (field.auto_now or field.auto_now_add):
            return True
        if field.primary_key:
            return True
        return False

    @classmethod
    def is_field_required(cls, field: models.Field) -> bool:
        """
        Checks if field is required and create-blocking for model
        :param field:
        :return: True if required
        """
        if field.name == 'id' or field.default != NOT_PROVIDED or \
                isinstance(field, models.DateField) or isinstance(field, models.TimeField) and (
                field.auto_now or field.auto_now_add):
            return False
        if isinstance(field, models.ManyToManyField):
            return False

        if field.blank or field.null:
            return False

        return True

    @staticmethod
    def all_subclasses(parent_class):
        from avishan.models import AvishanModel
        return set(parent_class.__subclasses__()).union(
            [s for c in parent_class.__subclasses__() for s in AvishanModel.all_subclasses(c)])


class AvishanModelFilterExtension:

    @classmethod
    def queryset_handler(cls, params: dict, queryset: QuerySet):
        queryset: QuerySet = cls.django_filter_class()(data=params, queryset=queryset).qs
        if 'sort' in params.keys():
            queryset = queryset.order_by(*params['sort'][1:-1].split(","))
        if 'page' in params.keys():
            paginator = Paginator(queryset, per_page=params.get('page_size', 20))
            try:
                page_object = paginator.page(int(params['page']))
            except PageNotAnInteger:
                page_object = paginator.page(1)
            except EmptyPage:
                page_object = paginator.page(paginator.num_pages)

            get_current_request().avishan.response['pagination'] = {
                'total_objects': paginator.count,
                'pages_count': paginator.num_pages,
                'has_next': page_object.has_next(),
                'has_previous': page_object.has_previous(),
                'start_index': page_object.start_index(),
                'end_index': page_object.end_index()
            }
            queryset = page_object.object_list
        return queryset

    @classmethod
    def django_filter_class(cls) -> Union[Type[django_filters.FilterSet], type]:
        from avishan.models import AvishanModel
        cls: Union[AvishanModel, AvishanModelFilterExtension]
        return type(
            cls.class_name() + "Filter",
            (django_filters.FilterSet,),
            cls._django_filter_class_properties()
        )

    @classmethod
    def _django_filter_class_properties(cls) -> dict:
        from avishan.models import AvishanModel
        cls: AvishanModel

        class_dict = {
            # 'title__search': django_filters.CharFilter(field_name='title', lookup_expr='icontains')
        }

        fields = []
        for field in cls.get_fields():
            class_dict = {**class_dict, **cls._django_filter_lookups_from_field(field)}
            fields.append(field.name)

        class_dict['Meta'] = type(
            'Meta',
            (),
            {
                'model': cls,
                'fields': fields
            }
        )
        # todo add relational fields directly to fields
        # https://django-filter.readthedocs.io/en/master/guide/usage.html#generating-filters-with-meta-fields

        return class_dict

    @classmethod
    def _django_filter_lookups_from_field(cls, field: Field) -> dict:
        data = {
            field.name + '__isnull': django_filters.BooleanFilter(field_name=field.name, lookup_expr='isnull')
        }
        # numerics
        if isinstance(field, (models.IntegerField, models.AutoField)):
            data[field.name] = django_filters.NumberFilter(field_name=field.name)
            data[field.name + '__gt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='gt')
            data[field.name + '__gte'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='gte')
            data[field.name + '__lte'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='lte')
            data[field.name + '__lt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='lt')

        # chars
        if isinstance(field, (models.CharField, models.TextField)):
            data[field.name] = django_filters.CharFilter(field_name=field.name, lookup_expr='iexact')
            data[field.name + '__search'] = django_filters.CharFilter(field_name=field.name, lookup_expr='icontains')
            data[field.name + '__in'] = django_filters.CharFilter(field_name=field.name, lookup_expr='in')
            data[field.name + '__startswith'] = django_filters.CharFilter(field_name=field.name,
                                                                          lookup_expr='istartswith')
            data[field.name + '__endswith'] = django_filters.CharFilter(field_name=field.name, lookup_expr='iendswith')

            # data[field.name + '__regex'] = django_filters.CharFilter(field_name=field.name, lookup_expr='regex') todo

        # date
        # todo what the fuck with shamsi
        if isinstance(field, models.DateField):
            data[field.name] = django_filters.DateFilter(field_name=field.name)
            data[field.name + '__year'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='year')
            data[field.name + '__year__gt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='year__gt')
            data[field.name + '__year__gte'] = django_filters.NumberFilter(field_name=field.name,
                                                                           lookup_expr='year__gte')
            data[field.name + '__year__lte'] = django_filters.NumberFilter(field_name=field.name,
                                                                           lookup_expr='year__lte')
            data[field.name + '__year__lt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='year__lt')
            data[field.name + '__month'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='month')
            data[field.name + '__month__gt'] = django_filters.NumberFilter(field_name=field.name,
                                                                           lookup_expr='month__gt')
            data[field.name + '__month__gte'] = django_filters.NumberFilter(field_name=field.name,
                                                                            lookup_expr='month__gte')
            data[field.name + '__month__lte'] = django_filters.NumberFilter(field_name=field.name,
                                                                            lookup_expr='month__lte')
            data[field.name + '__month__lt'] = django_filters.NumberFilter(field_name=field.name,
                                                                           lookup_expr='month__lt')
            data[field.name + '__day'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='day')
            data[field.name + '__day__gt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='day__gt')
            data[field.name + '__day__gte'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='day__gte')
            data[field.name + '__day__lte'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='day__lte')
            data[field.name + '__day__lt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='day__lt')

        if isinstance(field, (models.TimeField, models.DateTimeField)):
            data[field.name] = django_filters.TimeFilter(field_name=field.name)
            data[field.name + '__hour'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='hour')
            data[field.name + '__hour__gt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='hour__gt')
            data[field.name + '__hour__gte'] = django_filters.NumberFilter(field_name=field.name,
                                                                           lookup_expr='hour__gte')
            data[field.name + '__hour__lte'] = django_filters.NumberFilter(field_name=field.name,
                                                                           lookup_expr='hour__lte')
            data[field.name + '__hour__lt'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='hour__lt')
            data[field.name + '__minute'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='minute')
            data[field.name + '__minute__gt'] = django_filters.NumberFilter(field_name=field.name,
                                                                            lookup_expr='minute__gt')
            data[field.name + '__minute__gte'] = django_filters.NumberFilter(field_name=field.name,
                                                                             lookup_expr='minute__gte')
            data[field.name + '__minute__lte'] = django_filters.NumberFilter(field_name=field.name,
                                                                             lookup_expr='minute__lte')
            data[field.name + '__minute__lt'] = django_filters.NumberFilter(field_name=field.name,
                                                                            lookup_expr='minute__lt')
            data[field.name + '__second'] = django_filters.NumberFilter(field_name=field.name, lookup_expr='second')
            data[field.name + '__second__gt'] = django_filters.NumberFilter(field_name=field.name,
                                                                            lookup_expr='second__gt')
            data[field.name + '__second__gte'] = django_filters.NumberFilter(field_name=field.name,
                                                                             lookup_expr='second__gte')
            data[field.name + '__second__lte'] = django_filters.NumberFilter(field_name=field.name,
                                                                             lookup_expr='second__lte')
            data[field.name + '__second__lt'] = django_filters.NumberFilter(field_name=field.name,
                                                                            lookup_expr='second__lt')

        if isinstance(field, models.DateTimeField):
            data[field.name] = django_filters.IsoDateTimeFromToRangeFilter(field_name=field.name)

        return data


class AvishanModelDescriptorExtension:
    DEFAULT_CRUD_DICT = {
        'all': True,
        'create': True,
        'update': True,
        'remove': True,
        'get': True
    }

    @classmethod
    def _create_default_args(cls) -> List[Union[FunctionAttribute, DjangoFieldAttribute]]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return [DjangoFieldAttribute(target=item) for item in cls._meta.fields if not cls.is_field_readonly(field=item)]

    @classmethod
    def _update_default_args(cls) -> List[FunctionAttribute]:
        return cls._create_default_args()

    @classmethod
    def openapi_documented_fields(cls) -> List[str]:
        """Returns list of field names should be visible by openapi documentation

        :return: list of document visible fields
        :rtype: List[str]
        """
        from avishan.models import AvishanModel
        cls: AvishanModel
        total = list(cls._meta.fields + cls._meta.many_to_many)
        privates = []
        for item in cls.to_dict_private_fields:
            if not isinstance(item, str):
                privates.append(item.name)
            else:
                privates.append(item)

        return [field.name for field in total if field.name not in privates]

    @classmethod
    def _get_documentation_title(cls):
        from avishan.models import AvishanModel
        cls: AvishanModel
        return f'Get item of {cls.class_name()}'

    @classmethod
    def _get_documentation_description(cls):
        return None

    @classmethod
    def _get_documentation_response_bodies(cls) -> List[ResponseBodyDocumentation]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return [
            ResponseBodyDocumentation(
                title='Success',
                attributes=[Attribute(
                    name=stringcase.snakecase(cls.class_name()),
                    type=Attribute.TYPE.OBJECT,
                    type_of=cls
                )]
            ),
            ResponseBodyDocumentation(
                title='Item not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        ]

    @classmethod
    def _get_authenticate(cls) -> bool:
        from avishan.configure import get_avishan_config
        return get_avishan_config().CRUD_AUTHENTICATE.get(cls.class_name(), cls.DEFAULT_CRUD_DICT).get('get', True)

    @classmethod
    def _all_documentation_title(cls):
        from avishan.models import AvishanModel
        cls: AvishanModel
        return f'Get list of {cls.class_plural_name()}'

    @classmethod
    def _all_documentation_description(cls):
        return None

    @classmethod
    def _all_documentation_response_bodies(cls) -> List[ResponseBodyDocumentation]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return [
            ResponseBodyDocumentation(
                title='Success',
                attributes=[Attribute(
                    name=stringcase.snakecase(cls.class_plural_name()),
                    type=Attribute.TYPE.ARRAY,
                    type_of=cls
                )]
            )
        ]

    @classmethod
    def _all_authenticate(cls) -> bool:
        from avishan.configure import get_avishan_config
        return get_avishan_config().CRUD_AUTHENTICATE.get(cls.class_name(), cls.DEFAULT_CRUD_DICT).get('all', True)

    @classmethod
    def _create_documentation_title(cls):
        from avishan.models import AvishanModel
        cls: AvishanModel
        return f'Create {cls.class_name()}'

    @classmethod
    def _create_documentation_description(cls):
        return None

    @classmethod
    def _create_documentation_request_body_description(cls) -> Optional[str]:
        return None

    @classmethod
    def _create_documentation_request_body_examples(cls) -> List[RequestBodyDocumentation.Example]:
        return []

    @classmethod
    def _create_documentation_request_body(cls) -> RequestBodyDocumentation:
        from avishan.models import AvishanModel
        cls: AvishanModel
        if len(Function.load_args_from_signature(getattr(cls, 'create'))) > 0:
            args = Function.load_args_from_signature(getattr(cls, 'create'))
        else:
            args = cls._create_default_args()
        return RequestBodyDocumentation(
            attributes=args,
            description=cls._create_documentation_request_body_description(),
            examples=cls._create_documentation_request_body_examples()
        )

    @classmethod
    def _create_documentation_response_bodies(cls) -> List[ResponseBodyDocumentation]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        responses = [
            ResponseBodyDocumentation(
                title='Created',
                attributes=[Attribute(
                    name=stringcase.snakecase(cls.class_name()),
                    type=Attribute.TYPE.OBJECT,
                    type_of=cls
                )]
            )]

        unique_items = [item.name for item in cls.get_fields() if item.unique]
        unique_items.remove('id')
        if len(unique_items) > 0:
            responses.append(ResponseBodyDocumentation(
                title=f'Unique constraint failed for {" or ".join(unique_items)}',
                status_code=status.HTTP_418_IM_TEAPOT,
            ))
        return responses

    @classmethod
    def _create_authenticate(cls) -> bool:
        from avishan.configure import get_avishan_config
        return get_avishan_config().CRUD_AUTHENTICATE.get(cls.class_name(), cls.DEFAULT_CRUD_DICT).get('create', True)

    @classmethod
    def _update_documentation_title(cls):
        from avishan.models import AvishanModel
        cls: AvishanModel
        return f'Update {cls.class_name()}'

    @classmethod
    def _update_documentation_description(cls):
        return None

    @classmethod
    def _update_documentation_request_body_description(cls) -> Optional[str]:
        return None

    @classmethod
    def _update_documentation_request_body(cls) -> RequestBodyDocumentation:
        from avishan.models import AvishanModel
        cls: AvishanModel
        if len(Function.load_args_from_signature(getattr(cls, 'update'))) > 0:
            args = Function.load_args_from_signature(getattr(cls, 'update'))
        else:
            args = cls._update_default_args()
        return RequestBodyDocumentation(
            attributes=args,
            description=cls._update_documentation_request_body_description()
        )

    @classmethod
    def _update_documentation_response_bodies(cls) -> List[ResponseBodyDocumentation]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        responses = [
            ResponseBodyDocumentation(
                title='Updated',
                attributes=[Attribute(
                    name=stringcase.snakecase(cls.class_name()),
                    type=Attribute.TYPE.OBJECT,
                    type_of=cls
                )]
            ),
            ResponseBodyDocumentation(
                title='Item not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        ]

        unique_items = [item.name for item in cls.get_fields() if item.unique]
        unique_items.remove('id')
        if len(unique_items) > 0:
            responses.append(ResponseBodyDocumentation(
                title=f'Unique constraint failed for {" or ".join(unique_items)}',
                status_code=status.HTTP_418_IM_TEAPOT,
            ))
        return responses

    @classmethod
    def _update_authenticate(cls) -> bool:
        from avishan.configure import get_avishan_config
        return get_avishan_config().CRUD_AUTHENTICATE.get(cls.class_name(), cls.DEFAULT_CRUD_DICT).get('update', True)

    @classmethod
    def _remove_documentation_title(cls):
        from avishan.models import AvishanModel
        cls: AvishanModel
        return f'Remove item of {cls.class_name()}'

    @classmethod
    def _remove_documentation_description(cls):
        return "Returns deleted object."

    @classmethod
    def _remove_documentation_response_bodies(cls) -> List[ResponseBodyDocumentation]:
        from avishan.models import AvishanModel
        cls: AvishanModel
        return [
            ResponseBodyDocumentation(
                title='Success',
                attributes=[Attribute(
                    name=stringcase.snakecase(cls.class_name()),
                    type=Attribute.TYPE.OBJECT,
                    type_of=cls
                )]
            ),
            ResponseBodyDocumentation(
                title='Item not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        ]

    @classmethod
    def _remove_authenticate(cls) -> bool:
        from avishan.configure import get_avishan_config
        return get_avishan_config().CRUD_AUTHENTICATE.get(cls.class_name(), cls.DEFAULT_CRUD_DICT).get('remove', True)
