from avishan.decorators import AvishanTemplateViewDecorator


@AvishanTemplateViewDecorator(authenticate=False)
def avishan_doc(request):
    import json
    from avishan.libraries.openapi3.classes import OpenApi
    from django.shortcuts import render
    return render(request, 'avishan/swagger.html',
                  context={'data': json.dumps(OpenApi('0.0.0', 'Documentation').export_json())})
