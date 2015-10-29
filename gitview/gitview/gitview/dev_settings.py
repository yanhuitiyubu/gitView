# -*- coding: utf-8 -*-

from gitview.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gitview',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}

INSTALLED_APPS += (
    'south',
    'debug_toolbar',
)
