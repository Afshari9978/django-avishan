import inspect
import datetime
from enum import Enum, auto
from typing import List, Callable, Type

from django.db import models


class Model:

    def __init__(self, target: object, name: str):
        self.target = target
        self.name = name
        self.attributes: List[Attribute] = []
        self.methods: List[Method] = []

    @classmethod
    def sub_classes(cls) -> List[object]:
        # todo
        raise NotImplementedError()

    @classmethod
    def super_classes(cls) -> List[object]:
        # todo
        raise NotImplementedError()

    def __str__(self):
        return self.name


class DjangoModel(Model):
    """
    Model descriptor for django models. Not only AvishanModel inherited ones.
    """

    def __init__(self, target: models.Model):
        super().__init__(
            target=target,
            name=target._meta.object_name
        )
        self.attributes: List[DjangoFieldAttribute] = self.extract_attributes()
        self.methods = self.extract_methods()

    def extract_attributes(self) -> List['DjangoFieldAttribute']:
        """
        Extracts fields from model and create DjangoFieldAttribute from them.
        """

        # noinspection PyUnresolvedReferences
        items = sorted([DjangoFieldAttribute(target=field) for field in
                        list(self.target._meta.fields + self.target._meta.many_to_many)], key=lambda x: x.name)

        for i, item in enumerate(items):
            if item.name == 'id':
                beginning = items.pop(i)
                items = [beginning] + items
                break
        return items

    def extract_methods(self) -> List['Method']:
        """
        Extracts methods from model and create Method from them.
        """
        a = [Method(target=getattr(self.target, name)) for name in ['create', 'get', 'update', 'delete']]
        return a


class Function:
    def __init__(self, target):
        self.target = target
        self.name = target.__name__
        self.description = target.__doc__.strip() if target.__doc__ else None
        self.inputs: List[FunctionAttribute] = self.extract_inputs()
        self.outputs: FunctionAttribute = self.extract_outputs()

    def extract_inputs(self) -> List['FunctionAttribute']:
        """
        Extracts args for it's method. Using python "inspect" module.
        """
        data = []
        for key, value in dict(inspect.signature(self.target).parameters.items()).items():
            if key in ['kwargs', 'self', 'cls']:
                continue
            data.append(FunctionAttribute(value))
        return data

    def extract_outputs(self) -> 'FunctionAttribute':
        """
        Extracts method returning arguments to "Attribute" objects.
        """
        try:
            return FunctionAttribute(inspect.signature(self.target).return_annotation)
        except ValueError:
            return None

    def __str__(self):
        return self.name


class Method(Function):
    pass


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
        TYPE.FLOAT: (float, models.FloatField),
        TYPE.DATE: (datetime.date, models.DateField),
        TYPE.TIME: (datetime.time, models.TimeField),
        TYPE.DATETIME: (datetime.datetime, models.DateTimeField),
        TYPE.BOOLEAN: (bool, models.BooleanField),
        TYPE.OBJECT: (models.OneToOneField, models.ForeignKey, models.FileField),
        TYPE.FILE: (models.FileField,),
    }

    def __init__(self, name: str, representation_type: 'Attribute.TYPE', representation_type_of=None):
        self.name = name
        self.representation_type: Attribute.TYPE = representation_type
        """
        If representation type is OBJECT or ARRAY it can be defined.
        """
        self.representation_type_of = representation_type_of

    @staticmethod
    def type_finder(entry) -> 'Attribute.TYPE':
        for target, pool in Attribute._TYPE_POOL.items():
            if entry in pool:
                return target

        for target, pool in Attribute._TYPE_POOL.items():
            for swimmer in pool:
                if isinstance(entry, swimmer):
                    return target
        raise NotImplementedError()

    def __str__(self):
        return self.name


class DjangoFieldAttribute(Attribute):

    def __init__(self, target: models.Field):
        super().__init__(
            name=target.name,
            representation_type=self.define_representation_type(target)
        )
        if self.representation_type is Attribute.TYPE.OBJECT:
            if isinstance(target, (models.OneToOneField, models.ForeignKey)):
                self.representation_type_of = target.related_model
            else:
                raise NotImplementedError()
        if self.representation_type is Attribute.TYPE.ARRAY:
            raise NotImplementedError()
        self.target = target

    @property
    def is_required(self) -> bool:
        """
        Checks if field is required
        """
        if hasattr(self.target.model, 'is_field_required'):
            assert isinstance(self.target.model.is_field_required, Callable)
            return self.target.model.is_field_required(self.target)
        raise NotImplementedError()

    @staticmethod
    def define_representation_type(field: models.Field) -> Attribute.TYPE:
        """
        converts django fields models to defined types.
        :param field: target field
        """
        a = Attribute.type_finder(field.__class__)

        return a


class FunctionAttribute(Attribute):

    def __init__(self, parameter: inspect.Parameter):
        if parameter is inspect.Parameter.empty or parameter.name in ['self', 'cls']:
            raise ValueError

        super().__init__(
            name=parameter.name,
            representation_type=self.define_representation_type(parameter)
        )
        self.is_required = self.define_is_required(parameter)

    @staticmethod
    def define_representation_type(parameter: inspect.Parameter) -> Attribute.TYPE:
        return Attribute.type_finder(parameter.annotation)

    @staticmethod
    def define_is_required(parameter: inspect.Parameter):
        if parameter.default is not inspect.Parameter.empty:
            return False
        return True
