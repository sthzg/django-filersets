# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from filer.admin import ImageAdmin
from .category import *
from .filemodelext import *
from .item import *
from .set import *
from .settype import *


# Extend filer's image admin form.
ImageAdmin.inlines = ItemAdmin.inlines + [FilemodelExtInline]

# Register our admin models.
admin.site.register(Set, SetAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Settype, SettypeAdmin)
