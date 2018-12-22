DEBUG = True

import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

ROOT_URLCONF = 'travis-ci.urls'
WSGI_APPLICATION = 'travis-ci.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'persistent_message',
]

MIDDLEWARE = [                                                                  
    'django.contrib.sessions.middleware.SessionMiddleware',                     
    'django.middleware.common.CommonMiddleware',                                
    'django.middleware.csrf.CsrfViewMiddleware',                                
    'django.contrib.auth.middleware.AuthenticationMiddleware',                  
    'django.contrib.auth.middleware.RemoteUserMiddleware',                      
]                                                                               
                                                                                
AUTHENTICATION_BACKENDS = [                                                     
    'django.contrib.auth.backends.RemoteUserBackend',                           
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

STATIC_URL = '/static/'

USE_TZ = True
TIME_ZONE = 'UTC'
