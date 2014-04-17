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
    try:
        tag_name, root_id = token.split_contents()
        root_id = root_id.replace('"', '').replace("'", "")
    except ValueError:
        root_id = int(-1)

    return FSCategoryTree(root_id)


class FSCategoryTree(template.Node):
    """ Returns the rendered category tree """

    def __init__(self, root_id):
        self.root_id = root_id

#                                                                         ______
#                                                                         Render
    def render(self, context):
        """ """
        root_id = self.root_id
        lvl_compensate = 0

        # We support root id as value and as variable
        try:
            isinstance(int(self.root_id), int)
        except ValueError:
            try:
                root_id = template.Variable(root_id).resolve(context)
            except AttributeError:
                # TODO  Configurize if param errors should raise exception
                raise AttributeError('Invalid paramater for category root id')
            except template.VariableDoesNotExist:
                # TODO  Configurize if param errors should raise exception
                raise template.VariableDoesNotExist(
                    'Invalid paramater for category root id')

        request = context.get('request')
        t_settings = get_template_settings()

        if root_id < int(0):
            categories = Category.objects.get_categories_by_level()
        else:
            try:
                root_cat = Category.objects.get(pk=root_id)
                # TODO  Configurize include_self parameter
                categories = root_cat.get_descendants()
                lvl_compensate = root_cat.depth
            except Category.DoesNotExist:
                # TODO Templatize the no categories display
                return _('<p>No categories available</p>')

        # Check back base system, see views.py for documentation
        fs_referrer = request.session.get('fs_referrer', None)
        back_base_url = request.session.get('back_base_url', None)
        has_back_base = request.session.get('has_back_base', False)

        # -> Compile list items
        current_app = context.get('current_app')
        litems = list()
        for cat in categories:
            cat_slug_url = reverse(
                'filersets:list_view',
                kwargs=({'cat_slug': cat.slug_composed}),
                current_app=current_app)
            cat_id_url = reverse(
                'filersets:list_view',
                kwargs=({'cat_id': cat.pk}),
                current_app=current_app)
            cur_url = request.get_full_path()
            cat_classes = list()
            cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))
            if cur_url in (cat_slug_url, cat_id_url):
                cat_classes.append('active')

            if has_back_base and back_base_url in (cat_slug_url, cat_id_url):
                # Prevent marking two cats as active when switching categories
                if fs_referrer != '{}:list_view'.format(current_app):
                    cat_classes.append('active')

            t = get_template(t_settings['cat_tree_item'])
            c = Context({'cat': cat,
                         'cat_classes': ' '.join(cat_classes),
                         'current_app': current_app})
            litems.append(t.render(c))

        # -> Return them wrapped
        t = get_template(t_settings['cat_tree_wrap'])
        c = Context({'items': litems, 'current_app': current_app})
        return t.render(c)


# ______________________________________________________________________________
#                                                                   Registration
register.tag('fs_category_tree', do_category_tree)