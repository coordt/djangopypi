import os

from django.db import transaction
from django.http import (HttpResponseForbidden, HttpResponseBadRequest, 
                         HttpResponse, Http404)
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import MultiValueDict
from django.contrib.auth import login
from django.contrib.auth.models import User

from userpypi.decorators import basic_auth
from userpypi.forms import PackageForm, ReleaseForm
from userpypi.models import Package, Release, Distribution, Classifier
from userpypi.settings import (ALLOW_VERSION_OVERWRITE, METADATA_FIELDS, RELEASE_UPLOAD_TO)


ALREADY_EXISTS_FMT = _(
    "A file named '%s' already exists for %s. Please create a new release.")

def submit_package_or_release(user, post_data, files):
    """Registers/updates a package or release"""
    try:
        package = Package.objects.get(owner=user, name=post_data['name'])
    except Package.DoesNotExist:
        package = None

    package_form = PackageForm(post_data, instance=package)
    if package_form.is_valid():
        package = package_form.save(commit=False)
        package.owner = user
        package.save()
        for c in post_data.getlist('classifiers'):
            classifier, created = Classifier.objects.get_or_create(name=c)
            package.classifiers.add(classifier)
        if files:
            allow_overwrite = ALLOW_VERSION_OVERWRITE
            try:
                release = Release.objects.get(version=post_data['version'],
                                              package=package,
                                              distribution=RELEASE_UPLOAD_TO + '/' +
                                              files['distribution']._name)
                if not allow_overwrite:
                    return HttpResponseForbidden(ALREADY_EXISTS_FMT % (
                                release.filename, release))
            except Release.DoesNotExist:
                release = None

            # If the old file already exists, django will append a _ after the
            # filename, however with .tar.gz files django does the "wrong"
            # thing and saves it as package-0.1.2.tar_.gz. So remove it before
            # django sees anything.
            release_form = ReleaseForm(post_data, files, instance=release)
            if release_form.is_valid():
                if release and os.path.exists(release.distribution.path):
                    os.remove(release.distribution.path)
                release = release_form.save(commit=False)
                release.package = package
                release.save()
            else:
                return HttpResponseBadRequest(
                        "ERRORS: %s" % release_form.errors)
    else:
        return HttpResponseBadRequest("ERRORS: %s" % package_form.errors)

    return HttpResponse()

def authorize(request_user, owner_user, package):
    """
    Go through the checks to see if the user is authorized to perform any actions
    
    Returns: success, err_msg
    """
    MUST_CREATE = package is not None
    
    if owner_user.profile.organization:
        try:
            membership = request_user.memberships.get(team=owner_obj)
        except request_user.DoesNotExist:
            return False, 'You are not a member of team %s' % owner.username
        if MUST_CREATE and membership.permission < 3: # Can't create a new package
            return False, 'You can not create packages'
        if membership.permission == 1:
            return False, 'You can not update packages'
        return True, ''
    
    if request_user != owner_user:
        if MUST_CREATE:
            return False, "You can not create a package on someone else's account."
        try:
            maintainer = package.maintainers.get(user=request_user)
        except request_user.DoesNotExist:
            return False, 'You are not a maintainer of %s' % package.name
        if membership.permission == 1:
            return False, 'You can not update packages'
    return True, ''

@basic_auth
@transaction.commit_manually
def register_or_upload(request, owner=None):
    if request.method != 'POST':
        transaction.rollback()
        return HttpResponseBadRequest('Only post requests are supported')
    
    name = request.POST.get('name', None).strip()
    if not name:
        transaction.rollback()
        return HttpResponseBadRequest('No package name specified')
    
    version = request.POST.get('version', None).strip()
    metadata_version = request.POST.get('metadata_version', None).strip()
    if not version or not metadata_version:
        transaction.rollback()
        return HttpResponseBadRequest(
            'Release version and metadata version must be specified')
    if not metadata_version in METADATA_FIELDS:
        transaction.rollback()
        return HttpResponseBadRequest('Metadata version must be one of: %s' 
                                      (', '.join(METADATA_FIELDS.keys()),))
    
    try:
        owner_obj = User.objects.get(username=owner)
    except User.DoesNotExist:
        transaction.rollback()
        raise Http404
    
    try:
        package = Package.objects.get(owner=owner_obj, name=name)
    except Package.DoesNotExist:
        package = None
    
    authorized, err_msg = authorize(request.user, owner_obj, package)
    
    if not authorized:
        transaction.rollback()
        return HttpResponseForbidden(err_msg)
    
    if package is None:
        package = Package.objects.create(owner=owner_obj, name=name)
    
    release, created = Release.objects.get_or_create(package=package,
                                                     version=version)
    
    if (('classifiers' in request.POST or 'download_url' in request.POST) and 
        metadata_version == '1.0'):
        metadata_version = '1.1'
    
    release.metadata_version = metadata_version
    
    fields = METADATA_FIELDS[metadata_version]
    
    if 'classifiers' in request.POST:
        request.POST.setlist('classifier', request.POST.getlist('classifiers'))
    
    release.package_info = MultiValueDict(dict(filter(lambda t: t[0] in fields,
                                                      request.POST.iterlists())))
    
    for key, value in release.package_info.iterlists():
        release.package_info.setlist(key,
                                     filter(lambda v: v != 'UNKNOWN', value))
    
    release.save()
    
    if not 'content' in request.FILES:
        transaction.commit()
        return HttpResponse('release registered')
    
    uploaded = request.FILES.get('content')
    
    for dist in release.distributions.all():
        if os.path.basename(dist.content.name) == uploaded.name:
            """ Need to add handling optionally deleting old and putting up new """
            transaction.rollback()
            return HttpResponseBadRequest('That file has already been uploaded...')
    
    md5_digest = request.POST.get('md5_digest','')
    
    try:
        new_file = Distribution.objects.create(release=release,
                                               content=uploaded,
                                               filetype=request.POST.get('filetype','sdist'),
                                               pyversion=request.POST.get('pyversion',''),
                                               uploader=request.user,
                                               comment=request.POST.get('comment',''),
                                               signature=request.POST.get('gpg_signature',''),
                                               md5_digest=md5_digest)
    except Exception, e:
        transaction.rollback()
        print "Issue creating a Distribution", str(e)
        raise
    
    transaction.commit()
    
    return HttpResponse('upload accepted')

def list_classifiers(request, mimetype='text/plain'):
    response = HttpResponse(mimetype=mimetype)
    response.write(u'\n'.join(map(lambda c: c.name, Classifier.objects.all())))
    return response
