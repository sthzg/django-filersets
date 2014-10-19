# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django import template
from django.core.urlresolvers import reverse, resolve

register = template.Library()


def do_category_tree(parser, token):
    """
    If called without parameters, the whole category tree will be rendered.
    Optionally you can pass the pk of the category you wish to start with.
    """
    root_id = int(-1)
    skip_empty = False

    tokens = token.split_contents()

    if len(tokens) == 2:
        root_id = tokens[1].replace('"', '').replace("'", "")
    if len(tokens) == 3:
        skip_empty = bool(tokens[2].replace('"', '').replace("'", ""))

    return FSCategoryTree(root_id, skip_empty)


class FSCategoryTree(template.Node):
    """Returns the rendered category tree.

    :param root_id: id of root category
    :param skip_empty: flag whether to show links to empty categories
    """

    def __init__(self, root_id, skip_empty):
        self.root_id = root_id
        self.skip_empty = skip_empty

    def render(self, context):
        """Renders the category menu tree as HTML."""
        root_id = self.root_id
        skip_empty = self.skip_empty
        set_type = context.get('set_type')

        # We support root id as value and as variable
        try:
            isinstance(int(root_id), int)
        except ValueError:
            try:
                root_id = template.Variable(root_id).resolve(context)
            except AttributeError:
                raise AttributeError('Invalid parameter for category root id')
            except template.VariableDoesNotExist:
                raise template.VariableDoesNotExist(
                    'Invalid parameter for category root id')

        rev = reverse('filersets:partial_categorymenu')
        view, args, kwargs = resolve(rev)
        kwargs.update({
            'request': context.get('request'),
            'set_type_slug': set_type,
            'root_id': root_id,
            'skip_empty': skip_empty})

        return view(*args, **kwargs)


register.tag('fs_category_tree', do_category_tree)