from django.contrib import admin

from userpypi.models import *
from userpypi.settings import MIRRORING



admin.site.register(Package)
admin.site.register(Release)
admin.site.register(Classifier)
admin.site.register(Distribution)

if MIRRORING:
    admin.site.register(MasterIndex)
    admin.site.register(MirrorLog)
