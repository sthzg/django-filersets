# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ugettext
from filersets.admin.settype import SettypeInlineAdmin
from filersets.models import Category
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


def category_admin_form_clean(self):
    """Extends treebeard"s ModelForm clean w/ additional validation."""
    super(CategoryAdminForm, self).clean()

    if self.cleaned_data['_ref_node_id'] == 0:
        msg = _('You may not save a category to the root level.')
        raise ValidationError(msg)

    return self.cleaned_data

# This is treebeard's preferred way of creating a subclass of its ModelForm.
CategoryAdminForm = movenodeform_factory(Category)
CategoryAdminForm.clean = category_admin_form_clean


class CategoryAdmin(TreeAdmin):
    def watch_online(self, obj):
        """ Display link on change list to the category view on the website """
        cat_url = reverse('filersets:list_view',
                          kwargs={'cat_slug': obj.slug_composed})
        label = ugettext('Watch online')
        extra = 'icon-alpha5' if obj.number_of_sets() < int(1) else ''
        link = '<a href="{}"><span class="icon-eye-open {}"></span> {}</a>'
        return link.format(cat_url, extra, label)

    watch_online.allow_tags = True

    def try_to_move_node(self, as_child, node, pos, request, target):
        """Performs additional validation on node move."""
        # On node move we need to ensure, that...

        # a) ... a root node cannot be moved into a child level.
        # b) ... a child node cannot be moved into root level.
        # c) ... the composed slug remains unique within the new position.

        # Check a)
        if node.is_root():
            if pos != 'left' or not target.is_root():
                msg = _('Set type categories need to stay on the root level.')
                messages.error(request, msg)
                return HttpResponseBadRequest('Exception raised during move')

        # Check b)
        if not node.is_root():
            if target.is_root() and pos == 'left':
                msg = _('Categories cannot be moved to the root level.')
                messages.error(request, msg)
                return HttpResponseBadRequest('Exception raised during move')

        # Check c)
        # Depending on the mouse up target treebeard specifies the target's
        # position w/ different strings (see treebeard's admin). We need
        # to account for that when checking if we need to validate c).
        #
        # The use case in which we must not validate c) is when re-
        # ordering an item inside the same level. It then is no duplicated
        # slug and thus still unique.
        if 'child' in pos:
            items = target.get_children()
            target_depth = target.depth + 1
        else:
            items = target.get_siblings()
            target_depth = target.depth

        cond1 = node.get_root() != target.get_root()
        cond2 = node.depth != target_depth
        if cond1 or cond2:
            for child in items:
                if child.slug == node.slug:
                    msg = _('Category already exists on this level.')
                    messages.error(request, msg)
                    return HttpResponseBadRequest('Exception raised during move')

        return super(CategoryAdmin, self).try_to_move_node(
            as_child, node, pos, request, target)

    form = CategoryAdminForm
    list_display = ('name', 'number_of_sets', 'slug', 'is_active',)
    list_editable = ('is_active',)
    exclude = ('slug_composed', 'path', 'depth', 'numchild', 'parent',)
    inlines = [SettypeInlineAdmin]