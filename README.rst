=======
Avishan
=======

Avishan is a set of tools for building fast, comfortable and reliable django apps.

Quick start
-----------

1. Add "avishan" to end of your INSTALLED_APPS setting like this, and "AvishanMiddleware" to **end** of MIDDLEWARE too::

    INSTALLED_APPS = [
        ...
        'avishan',
    ]

    MIDDLEWARE = [
        ...
        'avishan_wrapper.middlewares.AvishanThreadStorage',
        'avishan.middlewares.AvishanMiddleware',
    ]

2. Include the avishan URLconf in your project urls.py like this::

    path('', include('avishan.urls')),

3. Run this commands to create the avishan models::

    python manage.py migrate
    python manage.py avishan_init

4. Now follow part below for more detail about every single usage.
