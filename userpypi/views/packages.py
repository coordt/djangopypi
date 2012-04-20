from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import Q
from django.http import Http404, HttpResponseRedirect
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView, create_update

from userpypi.decorators import user_owns_package, user_maintains_package
from userpypi.models import Package, Release
from userpypi.forms import SimplePackageSearchForm, PackageForm
from django.views.generic import ListView, DetailView, UpdateView
from userpypi.settings import PROXY_MISSING, PROXY_BASE_URL


class OwnerObjectMixin(object):
    def get_context_data(self, **kwargs):
        context = super(OwnerObjectMixin, self).get_context_data(**kwargs)
        context['owner'] = self.kwargs.get('owner', None)
        context['is_owner'] = self.owner == self.request.user.username
        return context
    
    def get_queryset(self):
        """
        Filter the queryset based on whether or not the requesting user is
        the owner of the requested objects
        """
        self.owner = self.kwargs['owner']
        
        if self.request.user.username != self.owner:
            params = dict(owner__username=self.owner, private=False)
        else:
            params = dict(owner=self.request.user)
        return self.model.objects.filter(**params)


class PackageListView(OwnerObjectMixin, ListView):
    model = Package
    context_object_name = 'package_list'
    simple = False
    owner = None
    
    def get_template_names(self):
        """
        Returns a list of template names to be used for the request. Must 
        return a list. May not be called if render_to_response is overridden.
        """
        if self.simple:
            return ['userpypi/package_list_simple.html']
        else:
            return ['userpypi/package_list.html']


class PackageDetailView(OwnerObjectMixin, DetailView):
    model = Package
    context_object_name = 'package'
    simple = False
    doap = False
    owner = None
    redirect = ''
    
    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response with a template rendered with the given context.
        """
        if self.redirect:
            return HttpResponseRedirect(self.redirect)
        
        self.doap = 'doap' in self.kwargs and self.kwargs['doap']
        
        if self.doap:
            response_kwargs['mimetype'] = 'text/xml'
        
        return super(PackageDetailView, self).render_to_response(
                                                    context, **response_kwargs)
    
    def get_object(self):
        package = self.kwargs.get('package', None)
        try:
            queryset = self.get_queryset().filter(name=package)
            obj = queryset.get()
        except ObjectDoesNotExist:
            if PROXY_MISSING:
                self.redirect = '%s/%s/' % (PROXY_BASE_URL.rstrip('/'), package)
                return None
            raise Http404(u"No %(verbose_name)s found matching the query" %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj
    
    def get_template_names(self):
        """
        Returns a list of template names to be used for the request. Must 
        return a list. May not be called if render_to_response is overridden.
        """
        if self.simple:
            return ['userpypi/package_detail_simple.html']
        elif self.doap:
            return ['userpypi/package_doap.xml']
        else:
            return ['userpypi/package_detail.html']


class PackageManageView(OwnerObjectMixin, UpdateView):
    model = Package
    form_class = PackageForm
    context_object_name = 'package'
    template_name = 'userpypi/package_manage.html'
    
    def dispatch(self, *args, **kwargs):
        return super(PackageManageView, self).dispatch(*args, **kwargs)
    
    def get_object(self):
        package = self.kwargs.get('package', None)
        try:
            queryset = self.get_queryset().filter(name=package)
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(u"No %(verbose_name)s found matching the query" %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

def search(request, **kwargs):
    if request.method == 'POST':
        form = SimplePackageSearchForm(request.POST)
    else:
        form = SimplePackageSearchForm(request.GET)
    kwargs.pop('owner')
    if form.is_valid():
        q = form.cleaned_data['query']
        kwargs['queryset'] = Package.objects.filter(owner=request.user).filter(
            Q(name__contains=q) | Q(releases__package_info__contains=q)).distinct()
    return PackageListView(request, **kwargs)


@user_maintains_package()
def manage_versions(request, package, **kwargs):
    kwargs.pop('owner')
    package = get_object_or_404(Package, owner=request.user, name=package)
    kwargs.setdefault('formset_factory_kwargs', {})
    kwargs['formset_factory_kwargs'].setdefault('fields', ('hidden',))
    kwargs['formset_factory_kwargs']['extra'] = 0

    kwargs.setdefault('formset_factory', inlineformset_factory(Package, Release, **kwargs['formset_factory_kwargs']))
    kwargs.setdefault('template_name', 'userpypi/package_manage_versions.html')
    kwargs.setdefault('template_object_name', 'package')
    kwargs.setdefault('extra_context', {})
    kwargs.setdefault('mimetype', settings.DEFAULT_CONTENT_TYPE)
    kwargs['extra_context'][kwargs['template_object_name']] = package
    kwargs.setdefault('formset_kwargs', {})
    kwargs['formset_kwargs']['instance'] = package

    if request.method == 'POST':
        formset = kwargs['formset_factory'](data=request.POST, **kwargs['formset_kwargs'])
        if formset.is_valid():
            formset.save()
            return create_update.redirect(kwargs.get('post_save_redirect', None),
                                          package)

    formset = kwargs['formset_factory'](**kwargs['formset_kwargs'])

    kwargs['extra_context']['formset'] = formset

    return render_to_response(kwargs['template_name'], kwargs['extra_context'],
                              context_instance=RequestContext(request),
                              mimetype=kwargs['mimetype'])
