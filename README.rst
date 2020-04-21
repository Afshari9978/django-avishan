=======
Avishan
=======

Avishan is a set of tools for building fast, comfortable and reliable django apps.

Quick start
-----------

1. On linux remember to install this packages::

    sudo apt-get install build-essential libffi-dev python3-pip python3-dev

2. Create virtual environment for your project::

    sudo -H pip3 install virtualenv

3. Just run this command::

    python manage.py avishan_config

Features
--------
* Request data storage (current_request dict)
* Auto-find and checks token from session, or request header
* Handle sort, search, filter and pagination on response
* Configure django settings.py file
* Handle CORS
* Creates config.py file for each app and project