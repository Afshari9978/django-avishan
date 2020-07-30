from django.http import JsonResponse
from django.shortcuts import render

from avishan.configure import get_avishan_config
from avishan.decorators import AvishanTemplateViewDecorator, AvishanApiViewDecorator


@AvishanTemplateViewDecorator(authenticate=False)
def avishan_doc(request):
    import json
    from avishan.libraries.openapi3.classes import OpenApi
    return render(request, 'avishan/swagger.html',
                  context={'data': json.dumps(OpenApi('0.0.0', 'Documentation').export_json())})


@AvishanApiViewDecorator(authenticate=False)
def avishan_chayi_create(request):
    from avishan.libraries.chayi import ChayiWriter
    ChayiWriter()
    return JsonResponse({'state': 'created'})


@AvishanTemplateViewDecorator(authenticate=False)
def avishan_redoc(request):
    from avishan.libraries.openapi3.rebuild import OpenApi

    open_api_yaml = OpenApi(
        application_title=get_avishan_config().OPENAPI_APPLICATION_TITLE,
        application_description=get_avishan_config().OPENAPI_APPLICATION_DESCRIPTION,
        application_version=get_avishan_config().OPENAPI_APPLICATION_VERSION,
        application_servers=get_avishan_config().OPENAPI_APPLICATION_SERVERS
    ).export_yaml()

    text_file = open('static/openapi.yaml', 'w+')
    text_file.write(open_api_yaml)
    text_file.close()
    return render(request, 'avishan/redoc.html')
