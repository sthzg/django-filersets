# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic.base import View
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from filersets.models import Set, Item


class ListView(View):
    """
    Show a list of sets using the configured templates.

    TODO    Fetch exceptions and handle empty lists
    TODO    Extend to be fully configurable
    TODO    Extend to handle category list views
    TODO    Extend to make use of paging
    """
    def get(self, request):

        fset = None
        list_items = list()

        for fset in Set.objects.all().order_by('-date'):
            fitems = (
                fitem
                for fitem in Item.objects.filter(set=fset).order_by('order')
            )

            t = get_template('filersets/list_item.html')
            c = Context({
                'set': fset,
                'items': fitems
            })
            list_items.append(t.render(c))

        return render(
            request,
            'filersets/list.html',
            {
                'fset': fset,
                'fitems': list_items
            }
        )


class SetView(View):
    """
    Show a detail page for a set.

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
            pass

        try:
            fset = Set.objects.get(**get_query)
        except ObjectDoesNotExist:
            raise Http404

        # TODO  We constantly need this -> Put it on the model manager
        fitems = (
            fitem
            for fitem in Item.objects.filter(set=fset).order_by('order')
        )

        return render(
            request,
            'filersets/set.html',
            {
                'fset': fset,
                'fitems': fitems,
            }
        )


class ProcessSetView(View):

    def get(self, request, set_id=None):
        """
        Process a set with the given set_id

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