# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from userpypi.feeds import ReleaseFeed
from userpypi.decorators import user_owns_package, basic_auth

from .views.packages import (PackageListView, PackageDetailView, 
                             PackageManageView, manage)
from .views.releases import ReleaseDetailView, ReleaseListView

urlpatterns = patterns('',

    # Basic Package Indexes
    url(r'^(?P<owner>[^/]+)/$',
        PackageListView.as_view(),
        name="userpypi-index"),
    url(r'^(?P<owner>[^/]+)/packages/$',
        PackageListView.as_view(), 
        name='userpypi-package-index'),
    url(r'^(?P<owner>[^/]+)/pypi/releases/$',
        ReleaseListView.as_view(),
        name='userpypi-release-list'),
    
    url(r'^(?P<owner>[^/]+)/search/$',
        'userpypi.views.packages.search',
        name='userpypi-search'),
    url(r'^(?P<owner>[^/]+)/rss/$', 
        ReleaseFeed(), 
        name='userpypi-rss'),
    
    # Simple indexes
    url(r'^(?P<owner>[^/]+)/simple/$',
        basic_auth(PackageListView.as_view(simple=True)),
        name='userpypi-package-index-simple'),
    url(r'^(?P<owner>[^/]+)/simple/(?P<package>[\w\d_\.\-]+)/?$',
        basic_auth(PackageDetailView.as_view(simple=True)),
        name='userpypi-package-simple'),
    
    # Regular Package Indexes
    url(r'^(?P<owner>[^/]+)/pypi/$', 
        'userpypi.views.root', 
        name="userpypi-root"),
    url(r'^(?P<owner>[^/]+)/pypi/(?P<package>[\w\d_\.\-]+)/?$',
        basic_auth(PackageDetailView.as_view()),
        name='userpypi-package'),
    url(r'^(?P<owner>[^/]+)/pypi/(?P<package>[\w\d_\.\-]+)/rss/$', 
        ReleaseFeed(),
        name='userpypi-package-rss'),    
    url(r'^(?P<owner>[^/]+)/pypi/(?P<package>[\w\d_\.\-]+)/doap.rdf$',
        PackageDetailView.as_view(doap=True),
        name='userpypi-package-doap'),
    url(r'^(?P<owner>[^/]+)/pypi/(?P<package>[\w\d_\.\-]+)/manage/$',
        manage,
        name='userpypi-package-manage'),
    url(r'^pypi/(?P<package>[\w\d_\.\-]+)/manage/versions/$',
        'userpypi.views.packages.manage_versions',
        name='userpypi-package-manage-versions'),
    
    # Release Indexes
    url(r'^(?P<owner>[^/]+)/pypi/(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/$',
        ReleaseDetailView.as_view(),
        name='userpypi-release'),
    url(r'^(?P<owner>[^/]+)/pypi/(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/doap.rdf$',
        ReleaseDetailView.as_view(doap=True),
        name='userpypi-release-doap'),
    url(r'^pypi/(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/manage/$',
        'userpypi.views.releases.manage',
        name='userpypi-release-manage'),
    url(r'^pypi/(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/metadata/$',
        'userpypi.views.releases.manage_metadata',
        name='userpypi-release-manage-metadata'),
    url(r'^pypi/(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/files/$',
        'userpypi.views.releases.manage_files',
        name='userpypi-release-manage-files'),
    url(r'^pypi/(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/files/upload/$',
        'userpypi.views.releases.upload_file',
        name='userpypi-release-upload-file'),
)