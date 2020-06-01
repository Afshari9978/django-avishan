from django.http import JsonResponse

from avishan.decorators import AvishanTemplateViewDecorator, AvishanApiViewDecorator


@AvishanTemplateViewDecorator(authenticate=False)
def avishan_doc(request):
    import json
    from avishan.libraries.openapi3.classes import OpenApi
    from django.shortcuts import render
    return render(request, 'avishan/swagger.html',
                  context={'data': json.dumps(OpenApi('0.0.0', 'Documentation').export_json())})


@AvishanApiViewDecorator(authenticate=False)
def avishan_chayi_create(request):
    from avishan.libraries.chayi import ChayiWriter
    ChayiWriter()
    return JsonResponse({'state': 'created'})
