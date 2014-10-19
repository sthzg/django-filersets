# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django import template
from django.template import Context
from django.template.loader import get_template
from filersets.config import get_template_settings
from filersets.models import Set

register = template.Library()


def do_setcategories(parser, token):
    """
    Supported arguments:

    ``fset``:
        Primary key of set or instance of set model.
    """
    tokens = token.split_contents()

    if len(tokens) == 2:
        fset = tokens[1].replace('"', '').replace("'", "")

    return FSSetCategories(fset)


class FSSetCategories(template.Node):
    """Returns the rendered category tree.

    :param root_id: id of root category
    :param skip_empty: flag whether to show links to empty categories
    """

    def __init__(self, fset):
        self.fset = fset

    def render(self, context):
        """Renders a list of categories that current set is assigned to."""
        fset = self.fset
        do_lookup = False

        # We support fset as primary key and as set instance.
        try:
            isinstance(int(fset), int)
            do_lookup = True
        except ValueError:
            try:
                fset = template.Variable(fset).resolve(context)
                do_lookup = True if isinstance(fset, int) else False
            except AttributeError:
                raise AttributeError('Invalid parameter for fset')
            except template.VariableDoesNotExist:
                raise template.VariableDoesNotExist(
                    'Invalid parameter for fset')

        if do_lookup:
            try:
                fset = Set.objects.get(pk=fset)
            except Set.DoesNotExist:
                return ''
        elif not do_lookup and not isinstance(fset, Set):
            return ''

        t_settings = get_template_settings(template_conf=fset.settype.template_conf)
        t = get_template(t_settings['set_categories'])
        c = Context({'categories': fset.get_categories(), 'fset': fset})

        return t.render(c)


register.tag('fs_setcategories', do_setcategories)