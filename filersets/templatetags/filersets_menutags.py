# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Python
from math import ceil, floor
# ______________________________________________________________________________
#                                                                         Django
from django import template
from django.template.loader import get_template
from django.template.context import Context
from django.core.urlresolvers import reverse
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Category

register = template.Library()


# ______________________________________________________________________________
#                                                                  Category Tree
def do_category_tree(parser, token):
    """
    """
    return FSCategoryTree()


class FSCategoryTree(template.Node):
    """ """
    def __init__(self):
        pass

    def render(self, context):
        """ """
        request = context.get('request')

        categories = Category.objects.get_categories_by_level()

        # Check back base system, see views.py for documentation
        fs_referrer = request.session.get('fs_referrer', None)
        back_base_url = request.session.get('back_base_url', None)
        has_back_base = request.session.get('has_back_base', False)

        # -> Compile list items
        litems = list()
        for cat in categories:
            cat_url = reverse(
                'filersets:list_view', kwargs=({'cat_slug': cat.slug_composed}))
            cur_url = request.get_full_path()
            cat_classes = list()
            cat_classes.append('cat-level-{}'.format(cat.level))
            if cat_url == cur_url:
                cat_classes.append('active')

            if has_back_base and back_base_url == cat_url:
                # Prevent marking two cats as active when switching categories
                if fs_referrer != 'filersets:list_view':
                    cat_classes.append('active')

            # TODO  Make template configurable
            t = get_template('filersets/templatetags/_category_tree_item.html')
            c = Context({'cat': cat, 'cat_classes': ' '.join(cat_classes)})
            litems.append(t.render(c))

        # -> Return them wrapped
        t = get_template('filersets/templatetags/_category_tree.html')
        c = Context({'items': litems})
        return t.render(c)


# ______________________________________________________________________________
#                                                                   Registration
register.tag('fs_category_tree', do_category_tree)