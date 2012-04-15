from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

import warnings

DEFAULT_SETTINGS = {
    'ALLOW_VERSION_OVERWRITE': False, # This is disabled on pypi.python.org, can be useful if you make mistakes
    'RELEASE_UPLOAD_TO': 'dists', # The upload_to argument for the file field in releases. This can either be a string for a path relative to your media folder or a callable.
    'RELEASE_FILE_STORAGE': settings.DEFAULT_FILE_STORAGE,
    'OS_NAMES': (
        ("aix", "AIX"),
        ("beos", "BeOS"),
        ("debian", "Debian Linux"),
        ("dos", "DOS"),
        ("freebsd", "FreeBSD"),
        ("hpux", "HP/UX"),
        ("mac", "Mac System x."),
        ("macos", "MacOS X"),
        ("mandrake", "Mandrake Linux"),
        ("netbsd", "NetBSD"),
        ("openbsd", "OpenBSD"),
        ("qnx", "QNX"),
        ("redhat", "RedHat Linux"),
        ("solaris", "SUN Solaris"),
        ("suse", "SuSE Linux"),
        ("yellowdog", "Yellow Dog Linux"),
    ),
    'ARCHITECTURES': (
        ("alpha", "Alpha"),
        ("hppa", "HPPA"),
        ("ix86", "Intel"),
        ("powerpc", "PowerPC"),
        ("sparc", "Sparc"),
        ("ultrasparc", "UltraSparc"),
    ),
    'DIST_FILE_TYPES': (
        ('sdist','Source'),
        ('bdist_dumb','"dumb" binary'),
        ('bdist_rpm','RPM'),
        ('bdist_wininst','MS Windows installer'),
        ('bdist_egg','Python Egg'),
        ('bdist_dmg','OS X Disk Image'),
    ),
    'PYTHON_VERSIONS': (
        ('any','Any i.e. pure python'),
        ('2.1','2.1'),
        ('2.2','2.2'),
        ('2.3','2.3'),
        ('2.4','2.4'),
        ('2.5','2.5'),
        ('2.6','2.6'),
        ('2.7','2.7'),
        ('3.0','3.0'),
        ('3.1','3.1'),
        ('3.2','3.2'),
    ),
    'METADATA_FIELDS': {
        '1.0': ('platform','summary','description','keywords','home_page',
                'author','author_email', 'license', ),
        '1.1': ('platform','supported_platform','summary','description',
                'keywords','home_page','download_url','author','author_email',
                'license','classifier','requires','provides','obsoletes',),
        '1.2': ('platform','supported_platform','summary','description',
                'keywords','home_page','download_url','author','author_email',
                'maintainer','maintainer_email','license','classifier',
                'requires_dist','provides_dist','obsoletes_dist',
                'requires_python','requires_external','project_url')
    },
    'METADATA_FORMS': {
        '1.0': 'userpypi.forms.Metadata10Form',
        '1.1': 'userpypi.forms.Metadata11Form',
        '1.2': 'userpypi.forms.Metadata12Form'
    },
    'FALLBACK_VIEW': 'userpypi.views.releases.index',
    'ACTION_VIEWS': {
        "file_upload": 'userpypi.views.distutils.register_or_upload', #``sdist`` command
        "submit": 'userpypi.views.distutils.register_or_upload', #``register`` command
        "list_classifiers": 'userpypi.views.distutils.list_classifiers', #``list_classifiers`` command
    },
    'XMLRPC_COMMANDS': {
        'list_packages': 'userpypi.views.xmlrpc.list_packages',
        'package_releases': 'userpypi.views.xmlrpc.package_releases',
        'release_urls': 'userpypi.views.xmlrpc.release_urls',
        'release_data': 'userpypi.views.xmlrpc.release_data',
        #'search': xmlrpc.search, Not done yet
        #'changelog': xmlrpc.changelog, Not done yet
        #'ratings': xmlrpc.ratings, Not done yet
    },
    'PROXY_BASE_URL': 'http://pypi.python.org/simple',
    'PROXY_MISSING': False,
    'MIRRORING': False,
}

USER_SETTINGS = DEFAULT_SETTINGS.copy()
USER_SETTINGS.update(getattr(settings, 'DJANGOPYPI_SETTINGS', {}))

ORIGINAL_SETTINGS = (
    'DJANGOPYPI_ALLOW_VERSION_OVERWRITE',
    'DJANGOPYPI_RELEASE_UPLOAD_TO',
    'DJANGOPYPI_OS_NAMES',
    'DJANGOPYPI_ARCHITECTURES',
    'DJANGOPYPI_DIST_FILE_TYPES',
    'DJANGOPYPI_PYTHON_VERSIONS',
    'DJANGOPYPI_METADATA_FIELDS',
    'DJANGOPYPI_METADATA_FORMS',
    'DJANGOPYPI_FALLBACK_VIEW',
    'DJANGOPYPI_ACTION_VIEWS',
    'DJANGOPYPI_XMLRPC_COMMANDS',
    'DJANGOPYPI_PROXY_BASE_URL',
    'DJANGOPYPI_PROXY_MISSING',
    'DJANGOPYPI_MIRRORING',
)

for setting in ORIGINAL_SETTINGS:
    value = getattr(settings, setting, False)
    if value:
        message = "%s is deprecated. Please use DJANGOPYPI_SETTINGS[%s] instead."
        new_setting = setting.replace('DJANGOPYPI_', '')
        warnings.warn(message % (setting, new_setting), DeprecationWarning)
        USER_SETTINGS[new_setting] = value
        globals()[setting] = value

globals().update(USER_SETTINGS)
