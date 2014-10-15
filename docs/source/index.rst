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
* django-cms 3.x


URL patterns
------------
* flersets_api: url(r'^filersets/api/', include('filersets.api_urls', namespace='filersets_api')),
* filersets: url(r'^filersets/', include('filersets.urls', namespace='filersets')),


Configuration options
---------------------

These are key|value pairs that live in ``FILERSETS_CONF``.

* ``no_categories`` (True|False)

Hides category selection from set edit view.

* ``no_date`` (True|False)

Hides date input from set edit view.

* ``no_description`` (True|False)

Hides description textarea from set edit view.


Template configuration
----------------------

[TODO]


Glossary
--------

Item
	Items are the smallest entity and (currently) directectly related to 
	a ``filer_file`` object. Thus they have access to all the (meta) data 
	provided by the ``filer_file`` and ``file`` object itself.

	Items can be of any file type, structured in arbitrary sub folders and
	sorted per set in the admin.

	In the future it is planned to support 'virtual' file objects like 
	database records and aliased files.


Set
	Sets are containers to bundle a number of items. E.g. an image gallery 
	bundles all images contained in it. The design goal is to make the set 
	a very flexible entity with support for nested sets and theming down to 
	any level.

	Sets can span any type of files and in the future should also be able 
	to contain non-file-like objects, e.g. database records.

	A set is tied to one filer base folder. All files and (and optionally 
	folders) are part of the set. Sets might have sub folders that 
	can be used to achieve a) further organization and b) a richt set of 
	templating choices (e.g. rendering media within a subfolder as 
	slideshows, etc.).


Set type
	Set types are used to create different *kinds* of sets. E.g., we might 
	wish to use ``filersets`` to manage all sorts of file collctions, e.g. 
	galleries, photo stories, press releases, downloads, blog posts, ...

	While all of these sets share their nature as being a collection of 
	(file) objects, they carry semanitcally different content. On a 
	system level, we will want

	– each of them to be available at different urls endpoints.
	– none/one/some of them as partials (e.g. blocks or streams)
	– none/one/some of them to provide additional fields like body text.
	– none/one/some of them have different categorization systems.
	– to proivde different templates.
	– to require differen permissions.

	All these aspect are enabled by grouping sets into different set types.


Category
	Categories proivde the opportunity of an extended categorization layer. 
	Downloads, for example, might fall into the category of logos, 
	photos, press material, business reports, etc.

	This can be achieved by using categories. Each category is a child of 
	its particular set type root category, which makes it possible to have 
	completely different and unrelated categories for set types.


Media stream
	The media stream is a concept to treat all items of one specific 
	set type as a unit. This enables developers to provide additional 
	functionality closely tied to the item level instead of the more 
	encapsulated level of individual sets. 

	A photographer for example might use a set type 'galleries' to 
	manage sets of media. Additionally she might want to ... 

	– select some of the media to be shown in a block, on home, etc.
	– assign tags, categories, stock portal links (really any kind of meta 
	data) in batch and independently from their location in different sets.


Timeline
	The timeline is a collection of items marked with a check on their 
	is_timeline checkbox. It enables devleopers to show a stream of items 
	that are manually selected by the content editor(s) to be visible on 
	this stream.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
