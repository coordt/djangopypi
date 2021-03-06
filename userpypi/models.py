import os
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson as json
from django.utils.datastructures import MultiValueDict
from django.contrib.auth.models import User

from userpypi.settings import (RELEASE_UPLOAD_TO, DIST_FILE_TYPES, 
    PYTHON_VERSIONS, DIST_FILE_TYPES, RELEASE_FILE_STORAGE)

from django.core.files.storage import get_storage_class

FILE_STORAGE = get_storage_class(RELEASE_FILE_STORAGE)

class PackageInfoField(models.Field):
    description = u'Python Package Information Field'
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['editable'] = False
        super(PackageInfoField,self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, basestring):
            if value:
                return MultiValueDict(json.loads(value))
            else:
                return MultiValueDict()
        if isinstance(value, dict):
            return MultiValueDict(value)
        if isinstance(value,MultiValueDict):
            return value
        raise ValueError('Unexpected value encountered when converting data to python')

    def get_prep_value(self, value):
        if isinstance(value,MultiValueDict):
            return json.dumps(dict(value.iterlists()))
        if isinstance(value, dict):
            return json.dumps(value)
        if isinstance(value, basestring) or value is None:
            return value

        raise ValueError('Unexpected value encountered when preparing for database')

    def get_internal_type(self):
        return 'TextField'

class Classifier(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    class Meta:
        verbose_name = _(u"classifier")
        verbose_name_plural = _(u"classifiers")
        ordering = ('name',)
        
    def __unicode__(self):
        return self.name


class Package(models.Model):
    owner = models.ForeignKey(User, related_name="packages_owned")
    name = models.CharField(max_length=255)
    auto_hide = models.BooleanField(_(u"Auto hide"), 
        default=True, 
        blank=False, 
        help_text="""Automatically hide previous releases when new releases 
                     are created.""")
    maintainers = models.ManyToManyField(
        User, 
        blank=True,
        related_name="packages_maintained",
        through='Maintainer')
    private = models.BooleanField(default=True)

    class Meta:
        verbose_name = _(u"package")
        verbose_name_plural = _(u"packages")
        get_latest_by = "releases__latest"
        ordering = ['name',]
        unique_together = ('owner', 'name',)
        permissions = (
            ('read_packages', 'Read Packages'),
            ('update_packages', 'Update Packages'),
            ('create_packages', 'Create Packages'),
            ('admin', 'Administrator'),
        )

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('userpypi-package', (), {
            'owner': self.owner.username, 
            'package': self.name
        })

    @property
    def latest(self):
        try:
            return self.releases.latest()
        except Release.DoesNotExist:
            return None

    def get_release(self, version):
        """Return the release object for version, or None"""
        try:
            return self.releases.get(version=version)
        except Release.DoesNotExist:
            return None

class Maintainer(models.Model):
    package = models.ForeignKey(Package)
    user = models.ForeignKey(User)
    permission = models.BigIntegerField(choices=enumerate(['Read Only', 'Read and Write']))


class Release(models.Model):
    package = models.ForeignKey(Package, related_name="releases", editable=False)
    version = models.CharField(max_length=128, editable=False)
    metadata_version = models.CharField(max_length=64, default='1.0')
    package_info = PackageInfoField(blank=False)
    hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = _(u"release")
        verbose_name_plural = _(u"releases")
        unique_together = ("package", "version")
        get_latest_by = 'created'
        ordering = ['-created']

    def __unicode__(self):
        return self.release_name

    @property
    def release_name(self):
        return u"%s-%s" % (self.package.name, self.version)

    @property
    def summary(self):
        return self.package_info.get('summary', u'')

    @property
    def description(self):
        return self.package_info.get('description', u'')

    @property
    def classifiers(self):
        return self.package_info.getlist('classifier')

    @models.permalink
    def get_absolute_url(self):
        return ('userpypi-release', (), {
            'owner': selfpackage.owner.username,
            'package': self.package.name,
            'version': self.version
        })


class Distribution(models.Model):
    release = models.ForeignKey(Release, related_name="distributions",
                                editable=False)
    content = models.FileField(upload_to=RELEASE_UPLOAD_TO, storage=FILE_STORAGE())
    md5_digest = models.CharField(max_length=32, blank=True, editable=False)
    filetype = models.CharField(max_length=32, blank=False,
                                choices=DIST_FILE_TYPES)
    pyversion = models.CharField(max_length=16, blank=True,
                                 choices=PYTHON_VERSIONS)
    comment = models.CharField(max_length=255, blank=True)
    signature = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    uploader = models.ForeignKey(User, editable=False, blank=True, null=True)

    @property
    def filename(self):
        return os.path.basename(self.content.name)

    @property
    def display_filetype(self):
        for key,value in DIST_FILE_TYPES:
            if key == self.filetype:
                return value
        return self.filetype

    @property
    def path(self):
        return self.content.name

    def get_absolute_url(self):
        return "%s#md5=%s" % (self.content.url, self.md5_digest)

    class Meta:
        verbose_name = _(u"distribution")
        verbose_name_plural = _(u"distributions")
        unique_together = ("release", "filetype", "pyversion")

    def __unicode__(self):
        return self.filename


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^userpypi\.models\.PackageInfoField"])
except ImportError:
    pass


class MasterIndex(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.title

class MirrorLog(models.Model):
    master = models.ForeignKey(MasterIndex, related_name='logs')
    created = models.DateTimeField(default='now')
    releases_added = models.ManyToManyField(Release, blank=True,
                                            related_name='mirror_sources')
    
    def __unicode__(self):
        return '%s (%s)' % (self.master, str(self.created),)
    
    class Meta:
        get_latest_by = "created"
