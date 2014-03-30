# django-filersets

  ```Status: experimental, currently under development.```

> django-filersets allows users to select one or more django filer directories and display their contents in a list and detail view. 

Filersets have various meta data like title, description, category and publishing date which makes them suitable to act as a thin wrapper around any collections of files. In the first step it is mainly used to create image galleries by uploading media in bulk using the original ``django-filer`` interface and afterwards create a set out of this folder.

## Next steps

Later steps on the roadmap will extend the core functionality to support more filetypes (video, audio, rST, markdown and HTML files), navigational logic for nested folder structures as well as different render methods.

## What and Why?

I find media management to be a critical part of web applications and a place were too many systems don't provide an accessible and centralized approach for developers, users and the server's file system. Filer offers a clean, intuitive and extendable way to handle editor-contributed media uploads including a very nice implementation of multifile uploads.

For websites I want editors to be able to handle and organize editor-contributed onsite-media exclusively in filer (from the model perspective). Oftentimes **users need a way to upload files in bulk and present them as some sort of collection**, like an image gallery. All the necessary meta data (like media title, media description and any number of extendable fields) for the individual items can be edited in filer's extendable media model. However, one feature that does not work that way is adding meta data for the whole set of files (the filer directory), including a set title, description, categories, tag, user permissions etc.

> This is were django-filersets comes in. It provides a set creation model to enter the data and be connected to one ore more filer directories. All files within these directories are then accessible as a set that can be displayed, f.i. in a list of all sets of a particular category, a sidebar, a set detail page, a Django CMS plugin,...


## Project status

Although many parts of the system are covered with test cases already I do consider this package still in early development. Whilst the current coverage sounds high I am aware of critical parts that need clever testing (one apsect that can not be messured in percentages). One of the next steps will be to provide screenshots and a demo of what is implemented so far. I hope that this step makes it easier for users to get an idea about the scope of this package. I'll see to how mature a system this grows and if it is as convenient to use as I hope. 

> If there is public interest, demand or feedback I am looking forward to it.
