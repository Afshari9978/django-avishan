import inspect
import datetime
from enum import Enum, auto
from typing import List, Callable, Type, Union, Optional, Tuple

import docstring_parser
import stringcase as stringcase
from django.db import models
from django.db.models.base import ModelBase
from djmoney.models.fields import MoneyField
from docstring_parser import DocstringMeta, DocstringParam


class Model:

    def __init__(self, target: Type[Union[models.Model, object]], name: str):
        self.target = target
        self.name = name
        self.long_description = None
        self.short_description = None
        self._doc = docstring_parser.parse(target.__doc__)
        self.attributes = []
        self.methods = []
        self.load_from_doc()

    def load_from_doc(self):
        self.short_description = self._doc.short_description
        self.long_description = self._doc.long_description

    def __str__(self):
        return self.name


class DjangoModel(Model):

    def __init__(self, target: Type[Union[models.Model, object]]):
        super().__init__(
            target=target,
            name=target._meta.object_name
        )
        self.attributes = self.extract_attributes()

    def extract_attributes(self) -> List['DjangoFieldAttribute']:
        """
        Extracts fields from model and create DjangoFieldAttribute from them.
        """

        return [DjangoFieldAttribute(target=item) for item in self.target._meta.fields]


class DjangoAvishanModel(DjangoModel):
    """
    Model descriptor for django models. Not only AvishanModel inherited ones.
    """

    def __init__(self, target: Type[models.Model]):
        super().__init__(target=target)

        self.prepare_docs()
        self.attributes = self.extract_attributes()
        self.methods = self.extract_methods()

    def prepare_docs(self):
        document_added_methods = []
        for method_name, method in inspect.getmembers(self.target, predicate=inspect.isfunction) + \
                                   inspect.getmembers(self.target, predicate=inspect.ismethod):
            if not method_name.endswith('_documentation_raw'):
                continue
            document_added_methods.append(method_name[1:-18])
        for method_name in document_added_methods:
            doc = getattr(self.target, f'_{method_name}_documentation_raw')()
            if hasattr(self.target, f'_{method_name}_documentation_params'):
                doc %= getattr(self.target, f'_{method_name}_documentation_params')()
            if inspect.ismethod(getattr(self.target, method_name)):
                getattr(self.target, method_name).__func__.__doc__ = doc
            else:
                getattr(self.target, method_name).__doc__ = doc

    def extract_attributes(self) -> List['DjangoFieldAttribute']:
        """
        Extracts fields from model and create DjangoFieldAttribute from them.
        """
        # todo should not be from openapi
        return [DjangoFieldAttribute(target=self.target.get_field(field_name)) for field_name in
                self.target.openapi_documented_fields()]

    def extract_methods(self) -> List['DirectCallable']:
        """
        Extracts methods from model and create Method from them.
        """
        return self.target.openapi_documented_methods()


class Function:

    def __init__(self, target):
        self.target = target
        self.name = target.__name__
        self.short_description: Optional[str] = None
        self.long_description: Optional[str] = None
        self.args: List[Attribute] = self.load_args_from_signature(self.target)
        self.returns: Optional[Attribute] = None
        self._doc = docstring_parser.parse(target.__doc__)
        if self.__class__ == Function:
            self.load_from_doc()

    def load_from_doc(self):
        """
        Caution: Override args only when doc have data about them. else keep signature data
        :return:
        :rtype:
        """
        raise NotImplementedError()

    @classmethod
    def load_args_from_signature(cls, method) -> List['Attribute']:
        args = []
        for key, value in dict(inspect.signature(method).parameters.items()).items():
            if key in ['self', 'cls', 'kwargs', 'avishan_raise_400']:
                continue
            args.append(FunctionAttribute(value))
        return args

    def __str__(self):
        return self.name


class Method(Function):

    def __init__(self, target):
        super().__init__(target)
        self.target_class = self.get_class_that_defined_method(target)
        self.is_class_method = inspect.ismethod(target)
        if self.__class__ == Method:
            self.load_from_doc()

    @staticmethod
    def get_class_that_defined_method(method):
        if inspect.ismethod(method):
            for cls in inspect.getmro(method.__self__.__class__):
                if cls.__dict__.get(method.__name__) is method:
                    return cls
            method = method.__func__
        if inspect.isfunction(method):
            cls = getattr(inspect.getmodule(method),
                          method.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
            if isinstance(cls, type):
                return cls
        return getattr(method, '__objclass__', None)


class ApiMethod(Method):
    class METHOD(Enum):
        GET = auto()
        POST = auto()
        PUT = auto()
        DELETE = auto()

    class RESPONSE:
        def __init__(self, returns: 'Attribute', description: str, status_code: int = 200, ):
            self.status_code = status_code
            self.returns = returns
            self.description = description

    def __init__(self, target, url: str, method: 'ApiMethod.METHOD'):
        super().__init__(target)
        self.responses: List[ApiMethod.RESPONSE] = []
        self.method: ApiMethod.METHOD = method
        self.url: str = url
        self.load_from_doc()

    def load_from_doc(self):
        self.short_description = self._doc.short_description
        self.long_description = self._doc.long_description
        if len(self._doc.params) > 0:
            self.args = [Attribute.create_from_doc_param(item) for item in self._doc.params]
        self.responses = self.load_responses_from_doc()

    def load_responses_from_doc(self) -> List['ApiMethod.RESPONSE']:
        responses = []
        for item in self._doc.meta:
            if not isinstance(item, DocstringMeta):
                continue
            if item.args[0] != 'response':
                continue
            responses.append(
                ApiMethod.RESPONSE(
                    returns=Attribute(
                        name='returns',
                        type=Attribute.create_type_from_doc_param(item.args[1]),
                        type_of=Attribute.create_type_of_from_doc_param(item.args[1])
                    ),
                    description=item.description,
                    status_code=int(item.args[2])
                )
            )
        return responses


class DirectCallable(ApiMethod):

    def __init__(self,
                 model: type,
                 target_name: str,
                 response_json_key: str = None,
                 request_json_key: str = None,
                 url: str = None,
                 method: ApiMethod.METHOD = ApiMethod.METHOD.GET,
                 authenticate: bool = True,
                 dismiss_request_json_key: bool = False,
                 dismiss_response_json_key: bool = False,
                 hide_in_redoc: bool = False,
                 is_class_method: bool = None,
                 on_empty_args: List['FunctionAttribute'] = None
                 ):
        from avishan.configure import get_avishan_config
        from avishan.models import AvishanModel
        model: AvishanModel
        if response_json_key is None:
            response_json_key = model.class_plural_snake_case_name()
        if request_json_key is None:
            request_json_key = model.class_snake_case_name()

        if url is None:
            auto_set_url = True
            url = f'/{target_name}'
        else:
            auto_set_url = False

        super().__init__(
            target=getattr(model, target_name),
            url='/' + get_avishan_config().AVISHAN_URLS_START + f'/{model.class_plural_snake_case_name()}' + url,
            method=method
        )

        self.target_class = model
        if self.short_description is None:
            self.short_description = stringcase.titlecase(self.target_class.class_name()) + " " + stringcase.titlecase(
                self.name)
        self.response_json_key = response_json_key
        self.request_json_key = request_json_key
        self.dismiss_request_json_key = dismiss_request_json_key if \
            method not in [ApiMethod.METHOD.GET, ApiMethod.METHOD.DELETE] else \
            True
        self.dismiss_response_json_key = dismiss_response_json_key
        self.authenticate = authenticate
        self.hide_in_redoc = hide_in_redoc
        if is_class_method is not None:
            self.is_class_method = is_class_method

        if not self.is_class_method and auto_set_url:
            self.url = '/' + get_avishan_config().AVISHAN_URLS_START + f'/{model.class_plural_snake_case_name()}/' \
                       + '{id}' + url

        if len(self.args) == 0 and on_empty_args:
            self.args = on_empty_args


class Attribute:
    """
    Defining Attributes details
    """

    class TYPE(Enum):
        """
        Types reduced to this standard and globally acceptable values
        """
        STRING = auto()
        INT = auto()
        FLOAT = auto()
        DATE = auto()
        TIME = auto()
        DATETIME = auto()
        BOOLEAN = auto()
        OBJECT = auto()
        ARRAY = auto()
        FILE = auto()

    """
    Type pool for checking targets
    """
    _TYPE_POOL = {
        TYPE.STRING: (str, models.CharField, models.TextField),
        TYPE.INT: (int, models.IntegerField, models.AutoField),
        TYPE.FLOAT: (float, models.FloatField, MoneyField),
        TYPE.DATE: (datetime.date, models.DateField),
        TYPE.TIME: (datetime.time, models.TimeField),
        TYPE.DATETIME: (datetime.datetime, models.DateTimeField),
        TYPE.BOOLEAN: (bool, models.BooleanField),
        TYPE.OBJECT: (models.OneToOneField, models.ForeignKey),
        TYPE.ARRAY: (list, List, tuple, Tuple),
        TYPE.FILE: (models.FileField,),
    }

    NO_DEFAULT = 'NO_DESCRIPTOR_DEFAULT'

    def __init__(self,
                 name: str,
                 type: 'Attribute.TYPE',
                 type_of: type = None,
                 default=NO_DEFAULT,
                 description: str = None,
                 example: str = None,
                 is_required: bool = True
                 ):
        self.name = name
        self.type: Attribute.TYPE = type
        """
        If representation type is OBJECT or ARRAY it can be defined.
        """
        self.type_of = type_of
        self.default = default
        self.description = description
        self.example = example
        self.is_required = is_required
        self._doc = None

    @classmethod
    def create_from_doc_param(cls, doc_param: DocstringParam) -> 'Attribute':
        return Attribute(
            name=doc_param.arg_name,
            type=Attribute.create_type_from_doc_param(doc_param.type_name),
            type_of=Attribute.create_type_of_from_doc_param(doc_param.type_name),
            description=doc_param.description,
            is_required=not doc_param.is_optional,
            default=doc_param.default
        )

    @classmethod
    def create_type_from_doc_param(cls, type_string: str) -> 'Attribute.TYPE':
        if type_string.find('[') > 0:
            return Attribute.type_finder(entry=type_string[:type_string.find('[')])

        return Attribute.type_finder(entry=type_string)

    @classmethod
    def create_type_of_from_doc_param(cls, type_string: str) -> Optional[type]:
        from avishan.models import AvishanModel

        if type_string.find('[') > 0:
            found = cls.create_type_from_doc_param(type_string=type_string)
            if found is Attribute.TYPE.ARRAY:
                return AvishanModel.get_model_with_class_name(type_string[type_string.find('[') + 1: -1])
        if isinstance(type_string, str):
            return AvishanModel.get_model_with_class_name(type_string)
        return None

    @staticmethod
    def type_finder(entry) -> 'Attribute.TYPE':
        from avishan.models import AvishanModel
        if entry == 'datetime.datetime':
            entry = datetime.datetime
        elif entry == 'datetime.date':
            entry = datetime.date
        elif entry == 'datetime.time':
            entry = datetime.time

        try:
            from typing import _Union
            if isinstance(entry, _Union):
                for item in entry.__args__:
                    return Attribute.type_finder(item)
        except ImportError:
            pass

        for target, pool in Attribute._TYPE_POOL.items():
            for swimmer in pool:
                if entry is swimmer:
                    return target

        # instanced type
        for target, pool in Attribute._TYPE_POOL.items():
            for swimmer in pool:
                if swimmer is str:
                    continue
                if isinstance(entry, swimmer):
                    return target

        # inherited type
        for target, pool in Attribute._TYPE_POOL.items():
            for swimmer in pool:
                if inspect.isclass(entry) and issubclass(entry, swimmer):
                    return target

        # string of type
        for target, pool in Attribute._TYPE_POOL.items():
            for swimmer in pool:
                if entry == swimmer.__name__:
                    return target

        if (isinstance(entry, str) and AvishanModel.get_model_with_class_name(entry) is not None) \
                or isinstance(entry, ModelBase):
            return Attribute.TYPE.OBJECT

        raise NotImplementedError()

    @staticmethod
    def type_caster(entry, target_type: 'Attribute.TYPE'):
        from avishan.models import AvishanModel

        if entry is None:
            return None

        if target_type is Attribute.TYPE.STRING:
            cast_class = str
        elif target_type is Attribute.TYPE.INT:
            cast_class = int
        elif target_type is Attribute.TYPE.FLOAT:
            cast_class = float
        elif target_type is Attribute.TYPE.DATETIME:
            cast_class = datetime.datetime
        elif target_type is Attribute.TYPE.DATE:
            cast_class = datetime.date
        elif target_type is Attribute.TYPE.BOOLEAN:
            cast_class = bool
        else:
            return entry

        return AvishanModel.cast_type_data(cast_class, entry)

    def __str__(self):
        return self.name


class DjangoFieldAttribute(Attribute):

    # todo default
    def __init__(self, target: models.Field):
        default = self.NO_DEFAULT
        if target.has_default():
            default = target.get_default()
        super().__init__(
            name=target.name,
            type=self.define_representation_type(target),
            description=target.help_text,
            default=default,
            is_required=self.check_is_required(target)
        )
        if self.type is Attribute.TYPE.OBJECT:
            if isinstance(target, (models.OneToOneField, models.ForeignKey)):
                self.type_of = target.related_model
            else:
                raise NotImplementedError()
        if self.type is Attribute.TYPE.ARRAY:
            raise NotImplementedError()
        if self.type is Attribute.TYPE.FILE:
            self.type = Attribute.TYPE.STRING
        self.target = target

    @classmethod
    def check_is_required(cls, target) -> bool:
        """
        Checks if field is required
        """
        if hasattr(target.model, 'is_field_required'):
            assert isinstance(target.model.is_field_required, Callable)
            return target.model.is_field_required(target)
        raise NotImplementedError()

    @staticmethod
    def define_representation_type(field: models.Field) -> Attribute.TYPE:
        """
        converts django fields models to defined types.
        :param field: target field
        """
        return Attribute.type_finder(field.__class__)


class FunctionAttribute(Attribute):

    # todo default
    def __init__(self, parameter: inspect.Parameter):
        from avishan.models import AvishanModel

        if parameter is inspect.Parameter.empty or parameter.name in ['self', 'cls']:
            raise ValueError

        default = self.NO_DEFAULT
        if parameter.default is not inspect.Parameter.empty:
            default = parameter.default
        super().__init__(
            name=parameter.name,
            type=self.define_representation_type(parameter),
            default=default
        )
        temp = parameter.annotation
        if self.type is Attribute.TYPE.OBJECT:
            if isinstance(parameter.annotation, str):
                self.type_of = AvishanModel.get_model_with_class_name(parameter.annotation)
            else:
                try:
                    from typing import _Union
                    if isinstance(parameter.annotation, _Union):
                        for item in parameter.annotation.__args__:
                            temp = item
                            break
                except Exception:
                    pass
                self.type_of = temp
        if self.type is Attribute.TYPE.ARRAY:
            temp = parameter.annotation.__args__[0]
            found_here = False
            try:
                from typing import _ForwardRef
                if isinstance(temp, _ForwardRef):
                    temp = AvishanModel.get_model_with_class_name(temp.__forward_arg__)
                    found_here = True
            except Exception:
                pass

            if not found_here:
                temp = Attribute.type_finder(temp)
            self.type_of = temp
        self.is_required = self.define_is_required(parameter)

    @staticmethod
    def define_representation_type(parameter: inspect.Parameter) -> Attribute.TYPE:
        return Attribute.type_finder(parameter.annotation)

    @staticmethod
    def define_is_required(parameter: inspect.Parameter):
        if parameter.default is not inspect.Parameter.empty:
            return False
        return True
