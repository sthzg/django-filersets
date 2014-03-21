# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.views.generic.base import View
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from filersets.models import Set, Item


class ListView(View):
    """
    Show a list of sets using the configured templates

    TODO    Fetch exceptions and handle empty lists
    TODO    Extend to be fully configurable
    TODO    Extend to handle category list views
    TODO    Extend to make use of paging
    """
    def get(self, request):

        list_items = list()
        for fset in Set.objects.all().order_by('created'):
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
                'list_page_title': _('List of Sets'),
                'list_items': list_items
            }
        )


class SetView(View):
    """
    Show a detail page for a set

    TODO    Check for set id or slug
    TODO    Create list and position aware back button handling
    """

    def get(self, request):

        return render(
            request,
            'filersets/list.html',
            {}
        )