from .base import *  # noqa

STOP_WORDS = (
    'a', 'an', 'and', 'if', 'is', 'the', 'in', 'i', 'you', 'other',
    'this', 'that', 'to',
)

# Django-allauth related settings
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django grappelli need to be added before django.contrib.admin
INSTALLED_APPS = (
                     'raven.contrib.django.raven_compat',
                     # enable Raven plugin
                     'grappelli',
                 ) + INSTALLED_APPS

# Grapelli settings
GRAPPELLI_ADMIN_TITLE = 'GeoContext Admin Page'

INSTALLED_APPS += (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'easyaudit',
    'rolepermissions',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework.authtoken',
    'corsheaders',
    'leaflet'
)

MIDDLEWARE += (
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
)

# Defines whether to log model related events,
# such as when an object is created, updated, or deleted
DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = True

# Defines whether to log user authentication events,
# such as logins, logouts and failed logins.
DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = True

# Defines whether to log URL requests made to the project
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = True

DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA = (
    'geocontext.Cache',
)

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (0, 10),
    'DEFAULT_ZOOM': 3,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'DEFAULT_PRECISION': 6,
    'MINIMAP': True,
    'TILES': [
        (
            'Basemap',
            'https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=Bik82wXesk2w368QAo9R',
            {
                'attribution': '<a href="https://www.maptiler.com/copyright/" target="_blank">© MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap contributors</a>',
                'crossOrigin': 'true'
            }
        ),
        (
            'Open street map',
            'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {
                'attribution': '<a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap contributors</a>',
                'crossOrigin': 'true'
            }
        ),
        (
            'Google streets',
            'http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            {
                'maxZoom': 18,
                'subdomains': ['mt0', 'mt1', 'mt2', 'mt3'],
                'attribution': 'Google &copy; Contributors',
                'crossOrigin': 'true'
            }
        ),
        (
            'Google hybrid',
            'http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',
            {
                'maxZoom': 18,
                'subdomains': ['mt0', 'mt1', 'mt2', 'mt3'],
                'attribution': 'Google &copy; Contributors',
                'crossOrigin': 'true'
            }
        ),
        (
            'Google satellite',
            'http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            {
                'maxZoom': 18,
                'subdomains': ['mt0', 'mt1', 'mt2', 'mt3'],
                'attribution': 'Google &copy; Contributors',
                'crossOrigin': 'true'
            }
        ),
        (
            'Google terrain',
            'http://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
            {
                'maxZoom': 18,
                'subdomains': ['mt0', 'mt1', 'mt2', 'mt3'],
                'attribution': 'Google, &copy; Contributors',
                'crossOrigin': 'true'
            }
        )
    ],
    'PLUGINS': {
        'leaflet-sidebar-v2': {
            'css': 'css/leaflet-sidebar-v2.css',
            'js': 'js/leaflet-sidebar-v2.js',
            'auto-include': True,
        }
    }
}

SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': ['user:email', 'public_repo', 'read:org']
    }
}

ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_SIGNUP_FORM_CLASS = 'base.forms.SignupForm'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
LOGIN_REDIRECT_URL = "/"

CORS_ORIGIN_ALLOW_ALL = True

RIVER_DATABASE = {
    'NAME': os.environ.get('RIVER_DATABASE_NAME'),
    'USER': os.environ.get('RIVER_DATABASE_USER'),
    'PASSWORD': os.environ.get('RIVER_DATABASE_PASSWORD'),
    'HOST': os.environ.get('RIVER_DATABASE_HOST'),
    'PORT': 5432,
}
