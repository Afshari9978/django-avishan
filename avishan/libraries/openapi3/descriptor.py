from typing import List

import yaml

from avishan.configure import get_avishan_config

from avishan.descriptor import Project, DjangoAvishanModel, DirectCallable, RequestBodyDocumentation, \
    ResponseBodyDocumentation


class OpenApi:
    def __init__(self,
                 application_title: str,
                 application_description: str = None,
                 application_version: str = '0.1.0',
                 application_servers: List['Server'] = None
                 ):
        self.application_title = application_title
        self.application_description = application_description
        self.application_version = application_version
        self.application_servers = application_servers
        self.project = Project(name=get_avishan_config().PROJECT_NAME)
        self.models: List[DjangoAvishanModel] = sorted(self.project.models_pool(), key=lambda x: x.name)

    def export(self) -> dict:
        data = {
            'openapi': '3.0.1',
            'info': self._export_info(),
            'servers': self._export_servers(),
            'tags': self._export_tags(),
            'paths': self._export_paths(),
            # 'components': self._export_components()
        }
        return data

    def _export_info(self):
        return {
            'title': self.application_title,
            'description': self.application_description,
            'version': self.application_version
        }

    def _export_servers(self):
        return [
            {
                'url': item.url,
                'description': item.description
            }
            for item in self.application_servers
        ]

    def _export_tags(self) -> list:
        total = []
        for model in self.models:
            if model.is_abstract() or model.name in get_avishan_config().get_openapi_ignored_path_models():
                continue
            data = {'name': model.name}
            if model.description:
                data['description'] = model.description
            total.append(data)
        return total

    def _export_paths(self) -> dict:
        data = {}

        for model in self.models:
            if model.name in get_avishan_config().get_openapi_ignored_path_models():
                continue
            for direct_callable in model.direct_callables:
                direct_callable: DirectCallable
                if direct_callable.hide_in_redoc:
                    continue
                if direct_callable.url not in data.keys():
                    data[direct_callable.url] = Path(url=direct_callable.url)
                setattr(data[direct_callable.url], direct_callable.method.name.lower(), Operation(
                    summary=direct_callable.short_description,
                    description=direct_callable.long_description,
                    request_body=Operation.extract_request_body_from_api_method(direct_callable),
                    responses=Operation.extract_responses_from_api_method(direct_callable),
                ))

        for key, value in data.items():
            data[key] = value.export()

        return data

    def export_yaml(self) -> str:
        return yaml.dump(self.export())


class Server:
    def __init__(self, url: str, description: str = None):
        self.url = url
        self.description = description

class RequestBody:
    def __init__(self, request_body_documentation: RequestBodyDocumentation):
        self.content = content
        self.required = required

    def export(self) -> dict:
        return {
            'content': self.content.export(),
            'required': self.required
        }


class Response:
    def __init__(self, response_body_documentation: ResponseBodyDocumentation):
        self.status_code = status_code
        self.description = description
        self.content = content

    def export(self) -> dict:
        data = {}
        if self.description:
            data['description'] = self.description
        if self.content:
            data['content'] = self.content.export()
        return data


class Operation:
    def __init__(self, direct_callable: DirectCallable):
        self.direct_callable: DirectCallable = direct_callable
        self.tags: List[str] = [self.direct_callable.target_class.class_name()]
        self.summary: str = self.direct_callable.documentation.title
        self.description: str = self.direct_callable.documentation.description
        self.request_body: RequestBody = RequestBody(self.direct_callable.documentation.request_body)
        self.responses: List[Response] = [Response(item) for item in self.direct_callable.documentation.response_bodies]

    def export(self) -> dict:
        data = {}
        if len(self.tags) > 0:
            data['tags'] = [item for item in self.tags]
        if self.summary:
            data['summary'] = self.summary
        if self.description:
            data['description'] = self.description
        if self.request_body:
            data['requestBody'] = self.request_body.export()
        if len(self.responses) > 0:
            data['responses'] = {}
            for item in self.responses:
                data['responses'][str(item.status_code)] = item.export()

        return data

class Path:
    def __init__(self,
                 url: str,
                 get: Operation = None,
                 post: Operation = None,
                 put: Operation = None,
                 delete: Operation = None,
                 ):
        self.url = url
        self.get = get
        self.post = post
        self.put = put
        self.delete = delete

    def export(self) -> dict:
        data = {}
        if self.get:
            data['get'] = self.get.export()
        if self.post:
            data['post'] = self.post.export()
        if self.put:
            data['put'] = self.put.export()
        if self.delete:
            data['delete'] = self.delete.export()

        return data
