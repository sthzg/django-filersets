# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from django.core.files import File as DjangoFile
from django.utils.timezone import now
from filer.models import File, Image, Folder
from filersets.models import Category, Settype, Set

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User



def create_superuser():
    """ Create a superuser for the test case """
    superuser = User.objects.create_superuser('admin',
                                              'sthzg@gmx.net',
                                              'secret')
    return superuser


def create_categories(depth=1, sibling=1, parent=None, cat_conf=None):
    """
    This method creates a category structure of the specified depths. ***It is
    in large parts taken from the original filer tests package.***

    :param depth: integer of levels to create for categories
    :param sibling: integer of siblings to created
    :param parent: None or Category object
    :param cat_conf: conf dict to specifically set inserted values
    """
    # TODO  Make inserted values configurable with `cat_conf` object
    if depth > 0 and sibling > 0:
        depth_range = list(range(1, depth+1))
        depth_range.reverse()
        for d in depth_range:
            for s in range(1, sibling+1):

                name = "category: %s -- %s" % (str(d), str(s))
                if not parent:
                    cat = Category.add_root(
                        is_active=True,
                        name=name,
                        description='',
                        parent=parent)
                else:
                    cat = parent.add_child(
                        is_active=True,
                        name=name,
                        description='',
                        parent=parent)

                create_categories(depth=d-1, sibling=sibling, parent=cat)

def create_controlled_categories():
    """
    Much like create_categories this provides a sample structure, with the only
    difference that this is manually controlled and easier for some of the
    tests to assert against.
    """
    set_type = create_set_type()

    cat01 = set_type.get_root_category()
    cat02 = cat01.add_child(is_active=True, name='Cat 01-01', description='', parent=None)
    cat03 = cat01.add_child(is_active=True, name='Cat 01-02', description='', parent=None)
    cat04 = cat03.add_child(is_active=True, name='Cat 01-02-01', description='', parent=None)
    cat05 = cat03.add_child(is_active=True, name='Cat 01-02-02', description='', parent=None)
    cat06 = cat01.add_child(is_active=True, name='Cat 02', description='', parent=None)
    cat07 = cat01.add_child(is_active=True, name='Cat 02-01', description='', parent=None)


def create_set_type():
    """
    Creates a SetType instance, which automatically creates a root category.
    """
    set_type = Settype(label='A set type')
    set_type.save()
    return set_type


def create_set(self, filer_root=None, filerdir_name='Filerset Tests',
               set_name='Filerset Tests', media_types=None,
               do_categorize=False, cat_config=None):
    """
    Creates a set with the given `set_name` and uploads all assets of given
    `media_types` to the filer test directory.

    In order to create this set we need to create dependencies in filer

    1.  Create filer directories: `/Filersets Tests/<filerdir_name>/'
    2.  Upload media to the newly created directory

    TODO   cat_config

    :param filer_root: the root folder for our operations in filer
    :param filerdir_name: the name of the directory in filer that is created
    :param set_name: the name of the set to be created in the test
    :param media_types: a list of configurable file types to add to the set
    :param do_categorize: flag whether to assign the set to a category or not
    :param cat_config: config-object to specify structure of categories
    """
    if not media_types:
        media_types = [{'all'}]

    category = None
    set_type = create_set_type()

    if do_categorize:
        if cat_config is None:
            create_categories(1, 1, parent=set_type.get_root_category())
            # We take the first child category beneath the auto-generated set
            # type category.
            category = Category.objects.all()[1]

    folder_root = Folder(name='Filerset Tests', parent=None)
    folder_root.save()
    folder_set = Folder(name=filerdir_name, parent=folder_root)
    folder_set.save()

    assets_dir = '{}{}'.format(os.path.abspath(os.path.dirname(__file__)),
                               '/assets/')

    # TODO Make the recursive import a feature
    parent = folder_set
    for (dirname, dirnames, filenames) in os.walk(assets_dir):
        # Create all folders
        # TODO  Respect the media_types parameter
        rel_path_tokens = dirname.replace(assets_dir, "").split(os.sep)
        get_query = {'name': rel_path_tokens[-1], 'parent_id': parent.pk}

        if rel_path_tokens[-1] != '':
            if Folder.contains_folder(parent, rel_path_tokens[-1]):
                parent = Folder.objects.get(**get_query)
            else:
                parent = Folder.objects.create(**get_query)

        # Save the file objects
        # TODO  Check file type and create Image or File accordingly
        for filename in filenames:
            furl = os.path.join(dirname,filename)
            file_obj = DjangoFile(open(furl, 'rb'), name=filename)
            image = Image.objects.create(owner=self.superuser,
                                         original_filename=filename,
                                         file=file_obj)

            file = File.objects.get(pk=image.file_ptr_id)
            file.folder_id = parent.pk
            file.save()

    fset = Set.objects.create(title=set_name, description='', date=now(),
                              folder=folder_set, status='published')
    if do_categorize:
        fset.category.add(category)
        fset.save()

    fset.create_or_update_set()
    return fset