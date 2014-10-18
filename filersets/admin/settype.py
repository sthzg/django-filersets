# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django import forms
from django.contrib import admin
from filersets.config import get_template_settings
from filersets.models import Settype


class SettypeModelForm(forms.ModelForm):
    class Meta:
        model = Settype

    def __init__(self, *args, **kwargs):
        """Provides filerset template config options in select widget."""
        super(SettypeModelForm, self).__init__(*args, **kwargs)

        if 'template_conf' not in self.Meta.exclude:
            choices = self.t_choices  # Populated in SettypeAdmin.get_form()
            self.fields['template_conf'].widget = forms.Select(choices=choices)


class SettypeAdmin(admin.ModelAdmin):
    form = SettypeModelForm
    list_display = ('label', 'memo',)
    exclude = ('category',)

    def get_form(self, request, obj=None, **kwargs):
        """Populates ``form.t_choices`` w/ available template choices.

        ``template_conf`` field is excluded if only one template is available.
        """
        t_settings = get_template_settings()
        choices = [(key, t_settings[key]['display_name']) for key in t_settings]
        self.form.t_choices = choices

        if len(choices) <= 1:
            self.exclude = list(self.exclude) + ['template_conf']

        return super(SettypeAdmin, self).get_form(request, obj, **kwargs)


class SettypeInlineAdmin(admin.StackedInline):
    """Adds set type settings as inline to category admin."""
    model = Settype.category.through
    extra = 0
    max_num = 1