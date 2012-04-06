from django.contrib import admin

from djangopypi.models import *
from djangopypi.settings import MIRRORING



admin.site.register(Package)
admin.site.register(Release)
admin.site.register(Classifier)
admin.site.register(Distribution)
admin.site.register(Review)

if MIRRORING:
    admin.site.register(MasterIndex)
    admin.site.register(MirrorLog)
