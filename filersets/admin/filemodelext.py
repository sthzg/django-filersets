from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.forms.models import ModelForm
from django.forms.widgets import SelectMultiple
from filersets.models import FilemodelExt
from .constants import *


class FilemodelExtForm(ModelForm):
    class Media:
        js = [JS_JQUERY_UI, JS_FILERSETS_ADMIN]
        css = {'all': [CSS_FILERSETS_ADMIN, CSS_FONTAWESOME]}

    class Meta:
        model = FilemodelExt
        widgets = {'category': SelectMultiple(attrs={'size': '9'})}


class FilemodelExtInline(admin.StackedInline):
    form = FilemodelExtForm
    model = FilemodelExt
    extra = 0
    max_num = 1
    can_delete = False