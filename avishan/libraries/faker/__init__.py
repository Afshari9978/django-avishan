import inspect
from datetime import datetime, date, time
from typing import Dict, Callable, Union, Optional
from inspect import Parameter

# todo fake_tree gets list of models needed to be faked. choose relation from themself not independent objects
from django.db import models
from faker import Faker

from avishan.configure import get_avishan_config


class AvishanFaker:
    _faker = Faker(locale=get_avishan_config().FAKER_LOCALE)
    Faker.seed(get_avishan_config().FAKER_SEED)

    @classmethod
    def fake_it(cls, **overriding):
        data = {}
        for key, value in cls.faker_get_create_params_dict().items():

            if callable(getattr(cls, f'_{key}_fake', None)):
                data[key] = getattr(cls, f'_{key}_fake')()
            else:
                if key in overriding.keys():
                    if callable(overriding[key]):
                        faking_method = overriding[key]
                    else:
                        faking_method = None
                else:
                    faking_method = cls.faker_assign_faking_method(key, value)

                if not faking_method:
                    data[key] = overriding[key]
                else:
                    data[key] = faking_method()

        created = cls.faker_get_create_method()(**data)
        if not hasattr(cls, 'fakes'):
            cls.fakes = []
        cls.fakes.append(created)
        return created

    @classmethod
    def fake_list(cls, count: int = 5, **overriding):
        return [cls.fake_it(**overriding) for _ in range(count)]

    @classmethod
    def faker_generate(cls, count: int = 5):
        if not hasattr(cls, 'fakes'):
            cls.fakes = []
        cls.fake_list(count=count - len(cls.fakes))
        return cls.fakes

    @classmethod
    def faker_get_create_params_dict(cls) -> Dict[str, Parameter]:
        return dict(inspect.signature(cls.faker_get_create_method()).parameters.items())

    @classmethod
    def faker_get_create_method(cls) -> Callable:
        from avishan.models import AvishanModel
        cls: Union[AvishanFaker, AvishanModel]
        return cls.create

    @classmethod
    def faker_assign_faking_method(cls, key: str, value: Parameter) -> Callable:
        from avishan.models import AvishanModel

        if not isinstance(value, Parameter):
            raise ValueError(f'parameter {key} in class {cls.__name__} should have type hint to fake it.')
        if key == 'kwargs':
            raise ValueError(f'kwargs in class {cls.__name__} is not valid')

        if value.default is None:
            return lambda: None

        if isinstance(value.annotation, models.base.ModelBase):
            if issubclass(value.annotation, AvishanModel):
                return lambda: value.annotation.fake_it()
            raise NotImplementedError()

        try:
            return {
                bool: cls._bool_fake,
                str: cls._str_fake,
                int: cls._int_fake,
                float: cls._float_fake,
                datetime: cls._datetime_fake,
                date: cls._date_fake,
                time: cls._time_fake
            }[value.annotation]
        except KeyError:
            pass

        if isinstance(value.annotation.__args__[0], ForwardRef):
            list_of = AvishanModel.get_model_with_class_name(value.annotation.__args__[0].__forward_arg__)
        else:
            list_of = value.annotation.__args__[0]
        return lambda: list_of.fake_list()

    @classmethod
    def _bool_fake(cls) -> bool:
        return cls._faker.pybool()

    @classmethod
    def _str_fake(cls) -> str:
        return " ".join(cls._faker.words(8))

    @classmethod
    def _int_fake(cls) -> int:
        return cls._faker.pyint(min_value=0, max_value=100000)

    @classmethod
    def _float_fake(cls,
                    left_digits: Optional[int] = 2,
                    right_digits: Optional[int] = 2,
                    positive: Optional[bool] = True,
                    min_value: Optional[float] = 0,
                    max_value: Optional[float] = None
                    ) -> float:
        return cls._faker.pyfloat(
            left_digits=left_digits,
            right_digits=right_digits,
            positive=positive,
            min_value=min_value,
            max_value=max_value
        )

    @classmethod
    def _datetime_fake(cls) -> datetime:
        return cls._faker.date_time()

    @classmethod
    def _date_fake(cls) -> date:
        return cls._faker.date_object()

    @classmethod
    def _time_fake(cls) -> time:
        return cls._faker.time_object()
