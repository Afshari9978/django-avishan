import inspect
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile, ZipInfo

import stringcase
from typing import Type, Dict

import typing
from django.db import models
from djmoney.models.fields import MoneyField

from avishan.configure import get_avishan_config
from avishan.models import AvishanModel


class ChayiWriter:
    def __init__(self):
        self.packs = []
        for item in get_avishan_config().CHAYI_PROJECT_PACKAGE:
            self.packs.append([item[0], f'package {item[1]}.models;\n\n'
                                        f'import {item[1]}.constants.Constants;\n'])

        self.files = {}
        self.tab_size = 0
        for model in AvishanModel.get_models():
            if model._meta.abstract or model.export_ignore:
                continue
            self.files[model.class_name() + ".java"] = self.model_file_creator(model)

        self.model_file_predefined_models(self.files)

        self.compress_files(self.packs, self.files)

    def model_file_creator(self, model: Type[AvishanModel]) -> str:
        data = self.model_file_head()

        data += f'\n\npublic class {model.class_name()} extends Chayi' + ' {\n\n'
        self.tab_size = 4

        data += self.model_file_write_fields(model)
        # data += self.model_file_write_constructor(model)
        data += self.model_file_write_copy_constructor(model)
        data += self.model_file_write_direct_callable_methods(model)
        data += self.model_file_write_getter_setters(model)
        data += self.model_file_write_names(model)

        data += '    @Override\n' \
                '    public boolean equals(Object o) {\n' \
                '        if (this == o) return true;\n' \
                '        if (o == null || getClass() != o.getClass()) return false;\n' \
                f'        {model.class_name()} temp = ({model.class_name()}) o;\n' \
                '        return this.id == temp.id;\n' \
                '    }\n'

        data += "}"

        return data

    @staticmethod
    def compress_files(packs: typing.List['str'], files: Dict[str, str]):
        for pack in packs:
            archive = BytesIO()
            with ZipFile(archive, 'w') as zip_archive:
                for key, value in files.items():
                    file = ZipInfo(key)
                    zip_archive.writestr(file, pack[1] + value)

            with open(f'static/chayi_models_{pack[0]}.zip', 'wb+') as f:
                # noinspection PyTypeChecker
                f.write(archive.getbuffer())

            archive.close()

    @staticmethod
    def model_file_head() -> str:
        return f'import ir.coleo.chayi.Chayi;\n' + ChayiWriter.model_file_head_imports()

    def tab_before(self) -> str:
        return self.tab_size * " "

    @staticmethod
    def model_file_head_imports() -> str:
        return get_avishan_config().CHAYI_MODEL_FILE_IMPORTS

    def model_file_write_fields(self, model: Type[AvishanModel]) -> str:
        data = ''
        for field in model.get_fields():
            if field.name == 'id':
                continue
            data += self.model_file_write_field(model, field)

        for name, python_type in model.to_dict_added_fields:
            data = self.model_file_write_added_to_dict(data, name, python_type)

        return data + "\n"

    def model_file_write_constructor(self, model: Type[AvishanModel]) -> str:
        # todo default values
        create_method = getattr(model, 'create')
        data = "\n" + self.tab_before() + \
               f'public {model.class_name()}('
        for name, param in dict(inspect.signature(create_method).parameters.items()).items():
            if param.name == 'kwargs':
                raise ValueError(f'Create function for model {model.class_name()} not found')
            data += f'{self.model_file_write_param_type(param.annotation)} {name}, '
        if data.endswith(', '):
            data = data[:-2]
        data += ") {\n"

        for name in dict(inspect.signature(create_method).parameters.items()):
            data += self.tab_before() + f"    this.{name} = {name};\n"
        data += self.tab_before() + "}\n"
        return data

    @staticmethod
    def model_file_write_copy_constructor(model: Type[AvishanModel]) -> str:
        data = f'    public {model.class_name()} () ' + "{}\n\n"

        data += f"    public {model.class_name()} ({model.class_name()} {model.class_snake_case_name()}) " + "{\n"
        for field in model.get_fields():
            data += f'        this.{field.name} = {model.class_snake_case_name()}.{field.name};\n'
        return data + "    }\n\n"

    def model_file_write_direct_callable_methods(self, model: Type[AvishanModel]) -> str:
        from avishan.descriptor import DirectCallable

        data = ''
        skip = ['all', 'create', 'update', 'remove', 'get']

        data += '    public static final boolean create_token = true;\n'
        for direct_callable in model.direct_callable_methods():
            if direct_callable.name in skip:
                continue
            if not direct_callable.authenticate:
                data += f'    public static final boolean {direct_callable.name}_token = false;\n'
            else:
                data += f'    public static final boolean {direct_callable.name}_token = true;\n'

        if inspect.ismethod(getattr(model, 'create')):
            data += '    public static final boolean create_on_item = false;\n'
        else:
            data += '    public static final boolean create_on_item = true;\n'

        for direct_callable in model.direct_callable_methods():
            direct_callable: DirectCallable
            if direct_callable.name in skip:
                continue
            if inspect.ismethod(direct_callable.target):
                data += f'    public static final boolean {direct_callable.name}_on_item = false;\n'
            else:
                data += f'    public static final boolean {direct_callable.name}_on_item = true;\n'

        data += '\n\n'

        method = getattr(model, 'create')
        # request
        data += f'    public static RequestBody create_request('
        for key, value in dict(inspect.signature(method).parameters.items()).items():
            if key in ['self', 'cls', 'kwargs', 'args']:
                continue
            data += f'{self.model_file_write_param_type(value.annotation)} {key}, '
        if data.endswith(', '):
            data = data[:-2]
        data += ") {\n"
        data += '        JsonObject wrapper = new JsonObject();'
        data += '        JsonObject object = new JsonObject();\n'
        data += f'        wrapper.add("{model.class_snake_case_name()}", object);'
        data += self.model_file_write_direct_callable_method_body(method)
        data += '        object = wrapper;'
        data += '        return RequestBody.create(MediaType.parse("json"), object.toString());\n    }\n\n'
        for direct_callable in model.direct_callable_methods():
            direct_callable: DirectCallable
            if direct_callable.name in skip:
                continue
            method = direct_callable.target
            # request
            data += f'    public static RequestBody {direct_callable.name}_request('
            for key, value in dict(inspect.signature(method).parameters.items()).items():
                if key in ['self', 'cls', 'kwargs', 'args']:
                    continue
                data += f'{self.model_file_write_param_type(value.annotation)} {key}, '
            if data.endswith(', '):
                data = data[:-2]
            data += ") {\n"
            if direct_callable.name == 'create':
                data += '        JsonObject wrapper = new JsonObject();'
            data += '        JsonObject object = new JsonObject();\n'
            if direct_callable.name == 'create':
                data += f'        wrapper.add("{model.class_snake_case_name()}", object);'
            data += self.model_file_write_direct_callable_method_body(method)
            if direct_callable.name == 'create':
                data += '        object = wrapper;'
            data += '        return RequestBody.create(MediaType.parse("json"), object.toString());\n    }\n\n'

        return data

    def model_file_write_direct_callable_method_body(self, method) -> str:
        data = ''

        for key, value in dict(inspect.signature(method).parameters.items()).items():
            if key in ['kwargs']:
                continue
            data = self.write_with_type_check(value.annotation, key, data)
        return data

    def write_with_type_check(self, annotation, key, text, null_checked: bool = False):
        if key in ['self', 'cls']:
            return text
        if null_checked:
            text += '    '
        # noinspection PyUnresolvedReferences
        if annotation in [str, int, bool, float]:
            text += f'        object.add("{key}", new JsonPrimitive({key}));\n'
        elif isinstance(annotation, typing._Union) and len(annotation.__args__) == 2:
            text += f'        if ({key} != null) ' + "{\n"
            text = self.write_with_type_check(annotation.__args__[0], key, text, True)
            text += '        }'
        elif isinstance(annotation, typing.GenericMeta) and isinstance(annotation.__args__[0], typing._ForwardRef):
            text += f'        JsonArray {key}_array = new JsonArray();\n'
            text += f'        for (Integer i = 0; i < {key}.size(); i++) ' + "{\n"
            text += f'            {key}_array.add(RetrofitSingleTone.getInstance().getGson().toJsonTree({key}.get(i)));\n'
            text += '        }\n'
            text += f'        object.add("{key}", {key}_array);\n'
        elif isinstance(annotation, models.base.ModelBase) or isinstance(annotation, str):
            text += f'        if ({key} == null) object.add("{key}", null);\n'
            text += f'        else ' + '{\n'
            text += f'            JsonObject {key}_object = new JsonObject();\n'
            text += f'            {key}_object.add("id", new JsonPrimitive({key}.getId()));\n'
            text += f'            object.add("{key}", {key}_object);\n'
            text += '        }\n'
        elif annotation is datetime:
            text += f'        if ({key} == null) object.add("{key}", null);\n'
            text += f'        else ' + '{\n'
            text += f'            JsonObject {key}_object = new JsonObject();\n'
            text += f'            {key}_object.add("year", new JsonPrimitive({key}.year));\n'
            text += f'            {key}_object.add("month", new JsonPrimitive({key}.month));\n'
            text += f'            {key}_object.add("day", new JsonPrimitive({key}.day));\n'
            text += f'            {key}_object.add("hour", new JsonPrimitive({key}.hour));\n'
            text += f'            {key}_object.add("minute", new JsonPrimitive({key}.minute));\n'
            text += f'            {key}_object.add("second", new JsonPrimitive({key}.second));\n'
            text += f'            {key}_object.add("microsecond", new JsonPrimitive({key}.microsecond));\n'
            text += f'            object.add("{key}", {key}_object);\n'
            text += '        }\n'

        else:
            raise NotImplementedError(annotation)
        return text

    def model_file_write_getter_setters(self, model: Type[AvishanModel]) -> str:
        data = ''
        for field in model.get_fields():
            if field.name == 'id':
                continue
            data += \
                f'    public {self.model_file_write_field_type(model, field)} ' \
                f'{stringcase.camelcase("get_" + field.name)}' \
                + "() {" + \
                f'\n        return {field.name};' \
                '\n    }' \
                '\n' \
                f'\n    public void ' \
                f'{stringcase.camelcase("set_" + field.name)}' \
                + f"({self.model_file_write_field_type(model, field)} {field.name}) " + "{" + \
                f'\n        this.{field.name} = {field.name};' \
                '\n    }' \
                '\n' \
                '\n'
        return data

    @staticmethod
    def model_file_write_names(model: Type[AvishanModel]) -> str:
        return f'\n    public static String getPluralName() ' \
               '{' \
               f'\n        return "{model.class_plural_snake_case_name()}";' \
               '\n    }' \
               '\n' \
               '\n    public static String getSingleName() {' \
               f'\n        return "{model.class_snake_case_name()}";' \
               '\n    }\n\n'

    def model_file_write_field(self, model: [AvishanModel], field: models.Field) -> str:
        data = self.tab_before() + '@Expose'
        if model.chayi_ignore_serialize_field(field):
            data += '(serialize = false)'
        data += '\n' + self.tab_before() + "protected " + \
                self.model_file_write_field_type(model, field) + " " + field.name + ";\n"

        return data

    def model_file_write_field_type(self, model: Type[AvishanModel], field: models.Field) -> str:

        if isinstance(field, (models.AutoField, models.IntegerField, MoneyField)):
            return 'Integer'
        if isinstance(field, models.ForeignKey):
            return field.related_model.__name__
        if isinstance(field, models.DateTimeField):
            return 'DateTime'
        if isinstance(field, (models.CharField, models.TextField)):
            return 'String'
        if isinstance(field, models.BooleanField):
            return 'boolean'
        if isinstance(field, models.FloatField):
            return 'double'
        if isinstance(field, models.ImageField):
            return 'Image'
        if isinstance(field, models.FileField):
            return 'File'
        raise NotImplementedError()

    # noinspection PyUnresolvedReferences
    def model_file_write_param_type(self, annotation: inspect.Parameter) -> str:
        if isinstance(annotation, models.base.ModelBase):
            return annotation.__name__
        if annotation is bool:
            return 'boolean'
        if annotation is str:
            return 'String'
        if annotation is int:
            return 'Integer'
        if annotation is float:
            return 'double'
        if annotation is datetime:
            return 'DateTime'
        if isinstance(annotation, str):
            return annotation
        if isinstance(annotation, typing._Union) and len(annotation.__args__) == 2:
            return self.model_file_write_param_type(annotation.__args__[0])
        if isinstance(annotation, typing.GenericMeta):
            return f'ArrayList<{self.model_file_write_param_type(annotation.__args__[0])}>'
        if isinstance(annotation, typing._ForwardRef):
            return annotation.__forward_arg__
        raise NotImplementedError()

    @staticmethod
    def model_file_predefined_models(files: dict):
        files['DateTime.java'] = """import ir.coleo.chayi.Chayi;

import com.google.gson.annotations.Expose;

public class DateTime {

    
    @Expose(serialize = false)
    public String day_name;
    @Expose(serialize = false)
    public String month_name;
    @Expose
    public Integer year;
    @Expose
    public Integer month;
    @Expose
    public Integer day;
    @Expose
    public Integer hour;
    @Expose
    public Integer minute;
    @Expose
    public Integer second;
    @Expose
    public Integer microsecond;
    
    public DateTime() {
    
    }
    
    public DateTime(DateTime datetime) {
        this.day_name = datetime.day_name;   
        this.month_name = datetime.month_name; 
        this.year = datetime.year;   
        this.month = datetime.month;  
        this.day = datetime.day;
        this.hour = datetime.hour;   
        this.minute = datetime.minute; 
        this.second = datetime.second; 
        this.microsecond = datetime.microsecond;
    }

}"""
        files['Date.java'] = """import ir.coleo.chayi.Chayi;

import com.google.gson.annotations.Expose;

public class Date {

    @Expose(serialize = false)
    public String day_name;
    @Expose(serialize = false)
    public String month_name;
    @Expose
    public Integer year;
    @Expose
    public Integer month;
    @Expose
    public Integer day;
                                  
}"""
        files['Time.java'] = """import ir.coleo.chayi.Chayi;

import com.google.gson.annotations.Expose;

public class Time {

    @Expose
    public Integer hour;
    @Expose
    public Integer minute;
    @Expose
    public Integer second;
    @Expose
    public Integer microsecond;

}"""
        files['Image.java'] = """import ir.coleo.chayi.Chayi;

import com.google.gson.annotations.Expose;

public class Image {

    @Expose(serialize = false)
    String file;
    @Expose
    Integer id;
    
    public Integer getId() {
        return id;
    }
    public String getFile() {
        return Constants.BASE_URL + file;
    }
    
}"""
        files['File.java'] = """import ir.coleo.chayi.Chayi;

import com.google.gson.annotations.Expose;

public class File {

    @Expose(serialize = false)
    String file;
    @Expose
    Integer id;
    
    public Integer getId() {
        return id;
    }
    
    public String getFile() {
        return Constants.BASE_URL + file;
    }

}"""

    # noinspection PyUnresolvedReferences
    def model_file_write_added_to_dict(self, data: str, name: str, python_type: Type[type]) -> str:

        data += '    @Expose(serialize = false)\n'
        if python_type == int:
            writing_type = 'Integer'
        elif python_type == str:
            writing_type = 'String'
        elif issubclass(python_type, typing.List) and isinstance(python_type.__args__[0], typing._ForwardRef):
            writing_type = f'ArrayList<{python_type.__args__[0].__forward_arg__}>'
        else:
            raise NotImplementedError()

        data += f'    public {writing_type} {name};\n'
        return data
