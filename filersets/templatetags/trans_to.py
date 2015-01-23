# -*- coding: utf-8 -*-
# Thanks to zalew @ http://stackoverflow.com/a/3177142/870769
from __future__ import absolute_import, unicode_literals
from django.utils import translation
from django.utils.translation import ugettext
from django.template import Library, Node,  Variable, TemplateSyntaxError
register = Library()


class TransNode(Node):
    def __init__(self, value, lc):
        self.value = Variable(value)
        self.lc = lc

    def render(self, context):
        translation.activate(self.lc)
        val = ugettext(self.value.resolve(context))
        translation.deactivate()
        context['trans_string'] = val
        return ''


def trans_to(parser, token):
    try:
        tag_name, value, lc = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    if not (lc[0] == lc[-1] and lc[0] in ('"', "'")):
        raise TemplateSyntaxError, "%r locale should be in quotes" % tag_name
    return TransNode(value, lc[1:-1])

register.tag('trans_to', trans_to)