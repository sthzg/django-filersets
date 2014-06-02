# -*- coding: utf-8 -*-
from django import dispatch

fset_processed = dispatch.Signal(providing_args=["fset"])