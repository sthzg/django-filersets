# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
# ______________________________________________________________________________
#                                                                            CMS
from menus.base import NavigationNode
from menus.menu_pool import menu_pool
from cms.menu_bases import CMSAttachMenu
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Category


class FilersetsCategoryMenu(CMSAttachMenu):

    name = _("filersets category menu")

    def get_nodes(self, request):

        nodes = []
        categories = Category.objects.get_categories_by_level(depth=1)
        for cat in categories:
            nn = NavigationNode(
                cat.name,
                reverse('filersets:list_view',
                        kwargs={'cat_slug': cat.slug_composed}),
                cat.pk,
                cat.parent_id)
            nodes.append(nn)

        return nodes

menu_pool.register_menu(FilersetsCategoryMenu)