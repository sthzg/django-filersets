# -*- coding: utf-8 -*-
from __future__ import absolute_import
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


class FilersetsApphook(CMSApp):
    name = _("Filersets App")
    urls = ["filersets.urls"]
    app_name = 'filersets'

apphook_pool.register(FilersetsApphook)