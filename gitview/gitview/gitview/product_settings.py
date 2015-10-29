import os

from gitview.settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

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

ADMINS = (
    ('Chenxiong Qi', 'cqi@redhat.com'),
)

# Following settings must be changed for server environment

PROJECT_DATA_ROOT = '/usr/share/gitview'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DATA_ROOT, 'templates'),
)

# Path to static files, that should be /usr/share/gitview/media
STATIC_ROOT = os.path.join(PROJECT_DATA_ROOT, 'static')


GITVIEW_DATA_ROOT = '/var/gitview'

#logging configuration
LOG_PATH = '/var/log/gitview'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s [%(module)s.%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%Y/%m/%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s',
            'datefmt': '%Y/%m/%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'infofile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'info.log'),
            'formatter': 'simple',
            'maxBytes' : 16 * 1024 * 1024,
            'backupCount': 5,
        },
        'errfile': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'err.log'),
            'formatter': 'verbose',
            'maxBytes' : 16 * 1024 * 1024,
            'backupCount': 5,
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
        },
        'views_logger': {
            'handlers': ['infofile', 'errfile'],
            'level': 'INFO',
            'propagate': True,
        },
        'commands_logger': {
            'handlers': ['infofile', 'errfile', 'console'],
            'level': 'INFO',
        },
    }
}

# Path to store PDF report files
PDF_REPORTFILES = os.path.join(GITVIEW_DATA_ROOT, 'pdfs')

# Viewapp will clone projects to this path
PROJECT_DIR = os.path.join(GITVIEW_DATA_ROOT, 'projects')
