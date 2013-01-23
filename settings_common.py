# Django settings for Boletango project.
import os.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DEBUG = True

DEVELOPMENT_HOST= 'Tofis-MacBook-Pro.local'
PRODUCTION_HOST = 'ip-10-212-229-108'


TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('Tofi', 'tofi.buzali@gmail.com'),
)

MANAGERS = ADMINS


DATABASES = {
	'default': {
			'ENGINE': 'django.db.backends.mysql',
			'NAME': 'boletango',
			'HOST': 'localhost',
			'USER': 'root',
			'PASSWORD': 'be%l13x:eVUXOFi',
			
	}
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True



# Make this unique, and don't share it with anybody.
SECRET_KEY = 'z4z2ok3^guq9ug4lg4gg*i+abyngv73p(lv=64n06ppa$^ry6&'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'Boletango.urls'



TEMPLATE_DIRS = (
	os.path.join(PROJECT_ROOT, "templates"),
    #"/Users/Tofi/Dropbox/Boletango/Django/Boletango/templates"
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
	'django.contrib.admin',

	'Boletango.Peliculas',
	'Boletango.API'
)

#SERIALIZATION_MODULES = {
#    'json': 'wadofstuff.django.serializers.json'
#}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
		'console':{
			'level': 'DEBUG',
			'class': 'logging.StreamHandler',
		},
		'file':{
			'level': 'DEBUG',
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': os.path.join(PROJECT_ROOT, "logs/log.txt"),
			'maxBytes': '1024',
			'backupCount': '3',
		}
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
		'Boletango.Peliculas':{
			'handlers': ['console', 'file'],
			'level': 'DEBUG',
			'propagate': True,
			
		
		}
    }
}


try:
    from local_settings import *
except ImportError:
    pass
