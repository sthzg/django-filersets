.. django-filesets documentation master file, created by
   sphinx-quickstart on Fri Mar 21 16:29:27 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-filesets's documentation!
===========================================

Contents:

.. toctree::
   :maxdepth: 2


    Status: Currently under development.


Dependencies
------------

* django-filer
* django-treebeard
* django-rest-framework
* django-extensions
* django-autoslug
* django-model-utils
* django-taggit

Optionally supported
--------------------
* django-suit
* django-taggit-autosuggest-select2


URL patterns
------------
* flersets_api: url(r'^filersets/api/', include('filersets.api_urls', namespace='filersets_api')),
* filersets: url(r'^filersets/', include('filersets.urls', namespace='filersets')),


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
