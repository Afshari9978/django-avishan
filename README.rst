=======
Avishan
=======

Avishan is a set of tools for building fast, comfortable and reliable django apps.

Quick start
-----------

0. On linux remember to install this packages::

    sudo apt-get install build-essential libffi-dev python3-dev

1. just run this command (::

    python manage.py avishan_config

Features
--------
* Request data storage (current_request dict)
* Auto-find and checks token from session, or request header
* Handle sort, search, filter and pagination on response
* Configure django settings.py file
* Handle CORS
* Creates config.py file for each app and project