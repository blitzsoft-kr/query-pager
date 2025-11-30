"""Django settings for tests."""

SECRET_KEY = 'test-secret-key'

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'tests.django_app',
]

USE_TZ = True
