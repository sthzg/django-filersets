# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.html import strip_tags
from django.views.generic.base import View
from django.template.context import Context
from django.template.loader import get_template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.http.response import HttpResponseRedirect, Http404
# ______________________________________________________________________________
#                                                                        Package
from filersets.config import get_template_settings
from filersets.models import Set, Item, Category


# ______________________________________________________________________________
#                                                                     View: List
class ListView(View):
    """ Show a list of sets using the configured templates.

    Global settings:
    You can configure the templates with these options in your settings:

    FILERSETS_TEMPLATES = {
        'base': '`path_to/another_base.html',
        'set': 'path_to/another_set.html',
        'list': 'path_to/another_list.html',
        'list_item': 'path_to/another_list_item.html',
    }

    Method call overrides
    TODO

    TODO    Use a view parameter to determine use specific templates

    TODO    Extend to be fully configurable
    TODO    Extend to make use of paging
    TODO    Extend to provide sorting
    """
    def get(self, request, cat_id=None, cat_slug=None):

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

            filter_query = {'category': cat}

        # Fetch sets by slug
        elif cat_slug:
            through_category = True
            # Asure that the generous url regexp is not explited
            cat_slug = strip_tags(cat_slug)
            try:
                cat = Category.objects.filter(slug_composed=cat_slug)[0]
            except IndexError:
                raise Http404

            filter_query = {'category': cat}

        # Fetch all sets
        else:
            filter_query = {}

        t_settings = get_template_settings()

        for fset in Set.objects.filter(**filter_query).order_by('-date'):
            fitems = (
                fitem
                for fitem in Item.objects.filter(set=fset).order_by('order')
            )

            t = get_template(t_settings['list_item'])
            c = Context({
                'set': fset,
                'items': fitems
            })
            list_items.append(t.render(c))

        if through_category:
            canonical_url = reverse('filersets:list_view', kwargs=({'cat_id': cat.pk}))
        else:
            canonical_url = reverse('filersets:list_view')

        return render(
            request,
            t_settings['list'],
            {
                't_extends': t_settings['base'],
                'fset': fset,
                'fitems': list_items,
                'canonical_url': canonical_url
            }
        )


# ______________________________________________________________________________
#                                                                      View: Set
class SetView(View):
    """ Show a detail page for a set.

    TODO    Check for set id or slug
    TODO    Create list and position aware back button handling
    """

    def get(self, request, set_id=None, set_slug=None):
        """

        :param set_id: pk of the set
        :param set_slug: slug of the set
        """

        if set_id:
            get_query = {'pk': int(set_id)}

        if set_slug:
            get_query = {'slug': set_slug}

        try:
            fset = Set.objects.get(**get_query)
        except ObjectDoesNotExist:
            raise Http404

        t_settings = get_template_settings()

        # TODO  We constantly need this -> Put it on the model manager
        fitems = (
            fitem
            for fitem in Item.objects.filter(set=fset).order_by('order')
        )

        return render(
            request,
            t_settings['set'],
            {
                't_extend': t_settings['base'],
                'fset': fset,
                'fitems': fitems,
            }
        )


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
            op_stats = Set.objects.create_or_update_set(int(set_id))
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
            {'op_stats': op_stats}
        )