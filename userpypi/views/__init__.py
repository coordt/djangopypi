from django.http import HttpResponseNotAllowed

from userpypi.decorators import csrf_exempt, basic_auth
from userpypi.http import parse_distutils_request
from userpypi.models import Package, Release
from userpypi.views.xmlrpc import parse_xmlrpc_request
from userpypi.settings import (FALLBACK_VIEW, ACTION_VIEWS)
from userpypi.utils import get_class, debug

@csrf_exempt
@debug
@basic_auth
def root(request, fallback_view=None, **kwargs):
    """ Root view of the package index, handle incoming actions from distutils
    or redirect to a more user friendly view """

    if request.method == 'POST':
        if request.META['CONTENT_TYPE'] == 'text/xml':
            return parse_xmlrpc_request(request)
        parse_distutils_request(request)
        action = request.POST.get(':action','')
    else:
        action = request.GET.get(':action','')
    if not action:
        if fallback_view is None:
            fallback_view = get_class(FALLBACK_VIEW)
        if hasattr(fallback_view, 'as_view'):
            return fallback_view.as_view()(request, **kwargs)
        return fallback_view(request, **kwargs)
    
    if not action in ACTION_VIEWS:
        print 'unknown action: %s' % (action,)
        return HttpResponseNotAllowed(ACTION_VIEWS.keys())
    
    return get_class(ACTION_VIEWS[action])(request, **kwargs)
