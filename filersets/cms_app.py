# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.utils.translation import ugettext_lazy as _
# ______________________________________________________________________________
#                                                                        Contrib
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


class FilersetsApphook(CMSApp):
    """
    Integration with Django CMS 3.

    Go to the advanced settings of a page in Django CMS 3 and choose the
    ``Filersets App`` Apphook. Enter filersets for the namespace.
    """

    # TODO  Try to separate all 3rd party support into own modules

    name = _("Filersets App")
    urls = ["filersets.urls"]
    app_name = 'filersets'

apphook_pool.register(FilersetsApphook)