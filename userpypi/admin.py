from django.contrib import admin

from userpypi.models import *
from userpypi.settings import MIRRORING

class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner',)
    search_fields = ('name',)

admin.site.register(Package, PackageAdmin)
admin.site.register(Release)
admin.site.register(Classifier)
admin.site.register(Distribution)

if MIRRORING:
    admin.site.register(MasterIndex)
    admin.site.register(MirrorLog)
