# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.db import models
from django import forms
from django.forms import widgets
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class TreeNodeCheckboxFieldRenderer(widgets.ChoiceFieldRenderer):
    choice_input_class = widgets.CheckboxChoiceInput

    def render(self):
        """Outputs a <ul> for this set of choice fields.

        Extends default behavior by rendering class attributes specific to
        the underlying tree structure.
        """
        id_ = self.attrs.get('id', None)
        start_tag = format_html('<ul class="fs_list-unstyled" id="{0}">', id_) if id_ else '<ul>'
        output = [start_tag]
        for idx, widget in enumerate(self):
            category = self.choices[idx][2]
            output.append(format_html('<li class="{}" data-is-root="{}" data-root-id="{}" data-level="{}">{}</li>',
                                      category.slug_composed,
                                      'true' if len(category.get_ancestors()) == int(0) else 'false',
                                      category.get_root().id,
                                      len(category.get_ancestors()),
                                      force_text(widget)))
        output.append('</ul>')
        return mark_safe('\n'.join(output))


class TreeNodeCheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    renderer = TreeNodeCheckboxFieldRenderer
    _empty_value = []


class CustomModelChoiceIterator(forms.models.ModelChoiceIterator):
    """Adds the model instance for each choice to the choice tuple.

    This is used on the renderer to create appropriate css class names for
    the choices in the rendered html.
    """
    def choice(self, obj):
        return (self.field.prepare_value(obj),
                self.field.label_from_instance(obj),
                obj,)


class TreeNodeMultipleChoiceField(forms.ModelMultipleChoiceField):
    """A ModelMultipleChoiceField for tree nodes."""
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return CustomModelChoiceIterator(self)

    choices = property(_get_choices, forms.ModelChoiceField._set_choices)


class TreeManyToManyField(models.ManyToManyField):
    """Model field for M2M fields that relate to treebeard instances."""
    def formfield(self, **kwargs):
        defaults = {
            'form_class': TreeNodeMultipleChoiceField,
            'choices_form_class': TreeNodeMultipleChoiceField}
        defaults.update(kwargs)
        return super(TreeManyToManyField, self).formfield(**kwargs)


# South integration
try:  # pragma: no cover
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^filersets\.fields\.TreeManyToManyField"])
except ImportError:
    pass