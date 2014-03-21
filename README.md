    Status: Currently under development.

**Filersets** is meant as a thin wrapper around **django filer**. It allows users to pick one or more django filer directories and display their contents in a collection and optionally a detail view (for example image galleries). The filerset model can have various meta data like title, description, category, publish date and is planned to have multiple render modes available.


##### Rationale

I find media management a critical part of web applications and a place were too many systems don't provide an accessible and centralized approach for developers, users and the server's file system. Filer offers a clean, intuitive and extendable way to handle editor-contributed media uploads including a very nice implementation of multifile uploads.

For websites I want editors to be able to handle and organize editor-contributed onsite-media exclusively in filer (from the model perspective). Oftentimes **users need a way to upload files in bulk and present them as some sort of collection**, like an image gallery. All the necessary meta data (like media title, media description and any number of extendable fields) for the individual items can be edited in filer's extendable media model. However, one feature that does not work that way is adding meta data for the whole set of files (the filer directory), including a set title, description, categories, tag, user permissions etc.

This is were django-filersets comes in. It provides a set creation model to enter the data and be connected to one ore more filer directories. All files within these directories are then accessible as as set that can be displayed, f.i. in a list of all sets of a particular category, a sidebar, a set detail page, a Django CMS plugin,...


##### Early development

Currently this is in very early development and I mostly pick the next targets out of features that I need right now in various projects. I'll see to how mature a system this grows and if it is as convenient to use as I hope. If there is public interest, demand or feedback I am looking forward to it.
