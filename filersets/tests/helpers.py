# -*- coding: utf-8 -*.
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.db import transaction

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Category


def create_superuser():
    """ Create a superuser for the test case """
    superuser = User.objects.create_superuser('admin',
                                              'sthzg@gmx.net',
                                              'secret')
    return superuser


def create_categories(depth=1, sibling=1, parent=None, cat_conf=None):
    """
    This method creates a category structure of the specified depths. ***It is
    in large parts taken from the original filer tests package***

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
                        is_active=False,
                        name=name,
                        description='',
                        parent=parent
                    )
                else:
                    cat = parent.add_child(
                        is_active=False,
                        name=name,
                        description='',
                        parent=parent
                    )

                # print cat.slug_composed
                create_categories(depth=d-1, sibling=sibling, parent=cat)