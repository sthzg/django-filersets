# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.contrib import messages
from django.shortcuts import render, render_to_response
from django.utils.html import strip_tags
from django.http.response import HttpResponseRedirect, Http404, HttpResponse
from django.template.loader import get_template
from django.core.exceptions import ObjectDoesNotExist
from django.template.context import Context, RequestContext
from django.core.urlresolvers import reverse, resolve
from django.views.generic.base import View
from django.utils.translation import ugettext_lazy as _
# ______________________________________________________________________________
#                                                                        Contrib
from rest_framework import viewsets
from filer.models import File
# ______________________________________________________________________________
#                                                                        Package
from filersets.config import get_template_settings
from filersets.models import Set, Item, Category, FilemodelExt
from filersets.serializers import (CategorySerializer,
                                   ItemSerializer,
                                   FileSerializer,
                                   FilemodelExtSerializer, FilersetSerializer)


# ______________________________________________________________________________
#                                                                     View: List
from rest_framework.decorators import api_view


class ListView(View):
    """ Show a list of sets using the configured templates.

    Global settings:
    You can configure the templates with these options in your settings:

    FILERSETS_TEMPLATES = {
        'base': '`path_to/another_base.html',
        'set': 'path_to/another_set.html',
        'list': 'path_to/another_list.html',
        'list_item': 'path_to/another_list_item.html',
        '<my_instance_namespace': {
            'list': 'path_to/another_list.html',
            'list_item': 'path_to/another_list_item.html',
        }
    }
    """
    # TODO    Use a view parameter to determine use specific templates
    # TODO    Extend to be fully configurable
    # TODO    Extend to make use of paging
    # TODO    Extend to provide sorting
    def get(self, request, cat_id=None, cat_slug=None):
        current_app = resolve(request.path).namespace
        fset = None
        through_category = False
        list_items = list()

        # Fetch sets by category primary key
        if cat_id:
            through_category = True
            try:
                cat = Category.objects.get(pk=cat_id)
            except ObjectDoesNotExist:
                raise Http404

            filter_query = {'category': cat,
                            'category__is_active': True,
                            'status': 'published'}

        # Fetch sets by slug
        elif cat_slug:
            through_category = True
            cat_slug = strip_tags(cat_slug)
            try:
                cat = Category.objects.filter(slug_composed=cat_slug)[0]
            except IndexError:
                raise Http404

            filter_query = {'category': cat,
                            'category__is_active': True,
                            'status': 'published'}

        # Fetch sets that are affiliated with the current instance namespace
        # See the Settype model in models.py for more information.
        else:
            cat_ids = [
                cat.pk
                for cat in Category.objects.filter(
                    settype_categories__namespace=current_app)]
            filter_query = {'category__in': cat_ids, 'status': 'published'}

        t_settings = get_template_settings(namespace=current_app)

        for fset in Set.objects.filter(**filter_query).order_by('-date').distinct():
            # TODO  Respect order config on individual sets
            fitems = [
                fitem
                for fitem in Item.objects.filter(set=fset)
                                 .order_by(*['-is_cover']+[fset.ordering])]

            t = get_template(t_settings['list_item'])
            c = RequestContext(request,
                               {'set': fset,
                                'items': fitems,
                                'current_app': current_app})
            list_items.append(t.render(c))

        if through_category:
            canonical_url = reverse('filersets:list_view',
                                    current_app=current_app,
                                    kwargs=({'cat_id': cat.pk}))
        else:
            canonical_url = reverse('filersets:list_view',
                                    current_app=current_app)

        # The Back Base System: Retaining state through sessions
        # ----------------------------------------------------------------------
        # Sets can be accessed over multiple URLs, for example after clicking a
        # link on a category list page (/en/category/<cat_slug>), after watching
        # a tag list (/en/tags/<tag_slug>), ... Whenever users follow such
        # links the system should preserve correct navigational context.
        # In other words if accessing a set detail page from the category list
        # page, the category should still be highlighted in the menu tree.
        #
        # To enable this behavior we store the page that linked to a set view in
        # the session. This session can be accessed on the set page view to
        # determine which leafs in the menu system need to be rendered active.
        #
        # If you have ideas for better solutions, feel free to drop an issue on
        # Github: https://github.com/sthzg/django-filersets
        # ----------------------------------------------------------------------
        request.session['has_back_base'] = True
        request.session['back_base_url'] = request.get_full_path()
        request.session['fs_referrer'] = '{}:list_view'.format(current_app)

        # The fs_last_pk cookie enables us to scroll to the list position of
        # the last clicked item (when coming back from a detail view)
        # Since we are on the list again, we can delete that entry here.
        try:
            del request.session['fs_last_pk']
        except KeyError:
            pass

        response = render(
            request,
            t_settings['list'], {
                't_extends': t_settings['base'],
                'fset': fset,
                'fitems': list_items,
                'canonical_url': canonical_url,
                'current_app': current_app})

        return response


# ______________________________________________________________________________
#                                                                      View: Set
class SetView(View):
    """ Show a detail page for a set. """
    # TODO  Support various predefined ordering options
    # TODO  Check for set id or slug
    # TODO  Create list and position aware back button handling
    def get(self, request, set_id=None, set_slug=None):
        """

        :param set_id: pk of the set
        :param set_slug: slug of the set
        """
        current_app = resolve(request.path).namespace
        request.session['fs_referrer'] = '{}:set_view'.format(current_app)

        if set_id:
            get_query = {'pk': int(set_id)}

        if set_slug:
            get_query = {'slug': set_slug}

        try:
            fset = Set.objects.get(**get_query)
            if fset.status != 'published':
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            raise Http404

        t_settings = get_template_settings()

        # TODO  Make ordering options available on set edit form
        fitems = (
            fitem
            for fitem in Item.objects.filter(set=fset)
                                     .order_by('item_sort__sort')
        )

        return render(
            request,
            t_settings['set'], {
                't_extend': t_settings['base'],
                'fset': fset,
                'fitems': fitems,
                'current_app': current_app})


# ______________________________________________________________________________
#                                                              View: Process Set
class ProcessSetView(View):

    def get(self, request, set_id=None):
        """ Process a set with the given set_id

        Certain GET query parameters can be given:
        ?redirect=<url> If set, redirects to this url and sets a message

        :param set_id: pk of the set
        """

        try:
            fset = Set.objects.get(pk=int(set_id))
            op_stats = fset.create_or_update_set()
        except:
            # TODO Exception handling
            pass

        if 'redirect' in request.GET:
            msg = _('Processed set with id {}').format(set_id)
            messages.add_message(request, messages.SUCCESS, msg)
            return HttpResponseRedirect(request.GET['redirect'])

        # TODO  Work on the output
        return render(
            request,
            'filersets/process_set.html',
            {'op_stats': op_stats})


# ______________________________________________________________________________
#                                                             API View: Category
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows categories to be viewed
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ______________________________________________________________________________
#                                                                 API View: Item
class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed and modified.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


# ______________________________________________________________________________
#                                                         API View: FilemodelExt
class FilemodelExtViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Filemodel Extensions to be viewed and modified.
    """
    queryset = FilemodelExt.objects.all()
    serializer_class = FilemodelExtSerializer


# ______________________________________________________________________________
#                                                                 API View: File
class FileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Filemodel Extensions to be viewed and modified.
    """
    queryset = File.objects.all()
    serializer_class = FileSerializer


class FilersetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows retrieving filerset instances.
    """
    queryset = Set.objects.all()
    serializer_class = FilersetSerializer