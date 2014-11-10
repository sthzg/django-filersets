# -*- coding: utf-8 -*-
from __future__ import absolute_import
from math import ceil, floor
from django import template
from django.conf import settings
from django.template.context import Context
from django.template.loader import get_template
from filersets.config import get_template_settings

register = template.Library()


def do_equal_height_cols(parser, token):
    """Renders a grid of list item displays w/ number of sets per row.

    ``fitems``
        Sets to display.

    ``num_cols``
        Number of cols to fit into one row.
    """

    try:
        tag_name, fitems, num_cols = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments"
                                           % token.contents.split()[0])

    if not (num_cols[0] == num_cols[-1]
            and num_cols[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name)

    return FSEqualHeightColsNode(fitems, num_cols[1:-1])


class FSEqualHeightColsNode(template.Node):
    """Node class for equal height set rendering."""
    def __init__(self, fitems, num_cols):
        self.fitems = template.Variable(fitems)
        self.num_cols = num_cols

    def render(self, context):
        """Renders a grid of list item displays w/ number of sets per row."""
        fitems = self.fitems.resolve(context)
        num_cols = int(self.num_cols)
        rows = int(ceil(len(fitems) / float(num_cols)))
        col_width = int(floor(settings.FILERSETS_GRID_TOTAL_COLS / num_cols))

        output = list()
        for idx in range(rows):
            start = idx * num_cols
            end = idx * num_cols + num_cols

            try:
                fitems[end]
            except IndexError:
                # fill empty spaces
                empty = '<div style="width:100%"><p>&nbsp;</p></div>'
                fill_up = [empty] * (end - len(fitems))
                fitems += fill_up

            # TODO  Template needs to be configurable
            t_settings = get_template_settings(template_conf='default')
            t = get_template(t_settings['equalheightcols'])
            c = Context({
                'idx_start': start,
                'idx_end': end,
                'num_cols': num_cols,
                'total_cols': settings.FILERSETS_GRID_TOTAL_COLS,
                'col_width': col_width,
                # TODO  This ties it to bootstrap, so we need a generic layer...
                'classes': ['col-md-{}'.format(num_cols)],
                'fitems': fitems[start:end],
            })

            output.append(t.render(c))

        context['set_rows'] = output
        return ''


register.tag('fs_equal_height_cols', do_equal_height_cols)