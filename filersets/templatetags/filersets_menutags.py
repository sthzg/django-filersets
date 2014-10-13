# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django import template
from django.template.loader import get_template
from django.template.context import Context
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Category
from filersets.config import get_template_settings

register = template.Library()


# ______________________________________________________________________________
#                                                                  Category Tree

#                                                                        _______
#                                                                        Compile
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
    """
    Returns the rendered category tree

    :param root_id: id of root category
    :param skip_empty: flag whether to show links to empty categories
    """

    def __init__(self, root_id, skip_empty):
        self.root_id = root_id
        self.skip_empty = skip_empty
#                                                                         ______
#                                                                         Render
    def render(self, context):
        """ Renders the category menu tree as HTML """
        root_id = self.root_id
        skip_empty = self.skip_empty
        set_type = context.get('set_type')
        request = context.get('request')
        t_settings = get_template_settings()

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

        if int(root_id) < int(0):
            categories = Category.objects.get_categories_by_level(
                skip_empty=skip_empty)
            lvl_compensate = int(0)
        else:
            try:
                root_cat = Category.objects.get(pk=root_id)
                lvl_compensate = root_cat.get_level_compensation()
                # TODO  Configurize include_self parameter
                categories = root_cat.get_descendants()
            except Category.DoesNotExist:
                # TODO Templatize the no categories display
                return _('<p>No categories available</p>')

        # Check back base system, see views.py for documentation
        fs_referrer = request.session.get('fs_referrer', None)
        back_base_url = request.session.get('back_base_url', None)
        has_back_base = request.session.get('has_back_base', False)

        litems = list()
        for cat in categories:
            cat_classes = list()
            cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))

            try:
                cat_set_type = cat.settype_categories.first().slug
            except AttributeError:
                pass

            cat_slug_url = reverse(
                'filersets:list_view',
                kwargs=({'set_type': cat_set_type,
                         'cat_slug': cat.slug_composed}),
                current_app=cat_set_type)

            cat_id_url = reverse(
                'filersets:list_view',
                kwargs=({'set_type': cat_set_type,
                         'cat_id': cat.pk}),
                current_app=cat_set_type)

            cur_url = request.get_full_path()

            if cur_url in (cat_slug_url, cat_id_url):
                cat_classes.append('active')

            if has_back_base and back_base_url in (cat_slug_url, cat_id_url):
                # Prevent marking two cats as active when switching categories
                if fs_referrer != '{}:list_view'.format(set_type):
                    cat_classes.append('active')

            t = get_template(t_settings['cat_tree_item'])
            c = Context({'cat': cat,
                         'cat_classes': ' '.join(cat_classes),
                         'set_type': cat_set_type})
            litems.append(t.render(c))

        t = get_template(t_settings['cat_tree_wrap'])
        c = Context({'items': litems, 'set_type': set_type})
        return t.render(c)


# ______________________________________________________________________________
#                                                                   Registration
register.tag('fs_category_tree', do_category_tree)