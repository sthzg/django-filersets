# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.http.response import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.template.context import RequestContext, Context
from django.template.loader import get_template
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from filer.models import File
from filersets.models import Settype
from rest_framework import viewsets
from .config import get_template_settings
from .models import Set, Item, Category, FilemodelExt
from .serializers import (CategorySerializer,
                          ItemSerializer,
                          FileSerializer,
                          FilemodelExtSerializer,
                          FilersetSerializer)


class ListView(View):
    """Show a list of sets using the configured templates."""
    # TODO    Use a view parameter to determine use specific templates
    # TODO    Extend to be fully configurable
    # TODO    Extend to make use of paging
    # TODO    Extend to provide sorting
    def get(self, request, cat_id=None, cat_slug=None, set_type=None):
        current_app = resolve(request.path).namespace

        if set_type:
            set_type_inst = Settype.objects.get(slug=set_type)
            template_conf = set_type_inst.template_conf
        else:
            try:
                # If we don't receive a set_type parameter with the slug we
                # try if the current app's namespace resolves to a set type.
                set_type_inst = Settype.objects.get(template_conf=current_app)
                set_type = set_type_inst.slug
                template_conf = current_app
            except Settype.DoesNotExist:
                template_conf = 'default'

        fset = None
        through_category = False
        list_items = list()

        # Fetch sets by category primary key
        if cat_id:
            through_category = True
            try:
                cat = Category.objects.get(pk=cat_id)
            except ObjectDoesNotExist:
                raise Http404

            filter_query = {
                'category': cat,
                'category__is_active': True,
                'status': 'published'
            }

        # Fetch sets by slug
        elif cat_slug:
            through_category = True
            cat_slug = strip_tags(cat_slug)
            slug = '/'.join([set_type, cat_slug])
            slug = '{}/'.format(slug) if slug[-1] != '/' else slug
            try:
                cat = Category.objects.filter(slug_composed=slug)[0]
            except IndexError:
                raise Http404

            filter_query = {
                'category': cat,
                'category__is_active': True,
                'status': 'published'
            }

        # Fetch sets that are affiliated with the current instance namespace
        # See the Settype model in models.py for more information.
        else:
            cat_ids = [
                cat.pk
                for cat in Category.objects.filter(
                    settype_categories__slug=set_type
                )
            ]

            filter_query = {'category__in': cat_ids}
            if not request.user.has_perm('can_edit'):
                filter_query.update({'status': 'published'})

        t_settings = get_template_settings(template_conf=template_conf)

        for fset in Set.objects.filter(**filter_query).order_by('-date').distinct():
            fitems = [
                fitem
                for fitem in Item.objects.filter(set=fset)
                                 .order_by(*['-is_cover']+['item_sort__sort'])
            ]

            t = get_template(t_settings['list_item'])
            c = RequestContext(
                request,
                {
                    'set': fset,
                    'items': fitems,
                    'set_type': set_type,
                    'current_app': current_app,
                }
            )
            list_items.append(t.render(c))

        if through_category:
            canonical_url = reverse('filersets:list_view',
                                    current_app=set_type,
                                    kwargs=({'set_type': set_type,
                                             'cat_id': cat.pk}))
        else:
            canonical_url = reverse('filersets:list_view',
                                    current_app=set_type)

        # The Back Base System: Retaining state through sessions
        # ----------------------------------------------------------------------
        # Sets can be accessed over multiple URLs, for example after clicking a
        # link on a category list page (/en/category/<cat_slug>), after watching
        # a tag list (/en/tags/<tag_slug>), ... Whenever users follow such
        # links the system should preserve correct navigational context.
        # In other words if accessing a set detail page from the category list
        # page, the category should still be highlighted in the menu tree.
        #
        # To enable this behavior we store the page that linked to a set view in
        # the session. This session can be accessed on the set page view to
        # determine which leafs in the menu system need to be rendered active.
        #
        # If you have ideas for better solutions, feel free to drop an issue on
        # Github: https://github.com/sthzg/django-filersets
        # ----------------------------------------------------------------------
        request.session['has_back_base'] = True
        request.session['back_base_url'] = request.get_full_path()
        request.session['fs_referrer'] = '{}:list_view'.format(set_type)

        # The fs_last_pk cookie enables us to scroll to the list position of
        # the last clicked item (when coming back from a detail view)
        # Since we are on the list again, we can delete that entry here.
        try:
            del request.session['fs_last_pk']
        except KeyError:
            pass

        response = render(
            request,
            t_settings['list'], {
                'base_extends': t_settings['base'],
                'fset': fset,
                'fitems': list_items,
                'canonical_url': canonical_url,
                'set_type': set_type,
                'current_app': current_app,
            }
        )

        return response


class SetView(View):
    """ Show a detail page for a set. """
    # TODO Check for set id or slug
    # TODO Create list and position aware back button handling
    def get(self, request, set_id=None, set_slug=None, set_type=None):
        user = request.user

        if set_type:
            set_type_instance = Settype.objects.get(slug=set_type)
            template_conf = set_type_instance.template_conf
        else:
            set_type = 'default'
            template_conf = 'default'

        request.session['fs_referrer'] = '{}:set_view'.format(set_type)

        if set_id:
            get_query = {'pk': int(set_id)}

        if set_slug:
            get_query = {'slug': set_slug}

        try:
            fset = Set.objects.get(**get_query)
            if fset.status != 'published' and not user.has_perm('can_edit'):
                raise ObjectDoesNotExist
        except Set.DoesNotExist:
            raise Http404

        t_settings = get_template_settings(template_conf=template_conf)

        fitems = (
            fitem for fitem in Item.objects.filter(
                set=fset
            ).order_by('item_sort__sort')
        )

        return render(
            request,
            t_settings['set'],
            {
                'base_extends': t_settings['base'],
                'fset': fset,
                'fitems': fitems,
                'set_type': set_type,
                'set_slug': set_slug,
            }
        )


class MediaView(View):
    """ Show a detail page for a set. """
    # TODO Check for set id or slug
    # TODO Create list and position aware back button handling
    def get(self, request, set_id=None, set_slug=None, set_type=None, media_id=None, media_slug=None):
        user = request.user

        if set_type:
            set_type_instance = Settype.objects.get(slug=set_type)
            template_conf = set_type_instance.template_conf
        else:
            set_type = 'default'
            template_conf = 'default'

        request.session['fs_referrer'] = '{}:set_view'.format(set_type)

        if set_id:
            get_query = {'pk': int(set_id)}

        if set_slug:
            get_query = {'slug': set_slug}

        try:
            fset = Set.objects.get(**get_query)
            if fset.status != 'published' and not user.has_perm('can_edit'):
                raise ObjectDoesNotExist
        except Set.DoesNotExist:
            raise Http404

        t_settings = get_template_settings(template_conf=template_conf)

        fitems = (
            fitem for fitem in Item.objects.filter(
                set=fset
            ).order_by('item_sort__sort')
        )

        if not media_id and not media_slug:
            return Http404

        try:
            fitem = Item.objects.get(pk=media_id)
        except Item.DoesNotExist:
            return Http404

        xmp = fitem.filer_file.file_xmpbase

        # Title
        title = 'Untitled'
        if fitem.title:
            title = fitem.title
        elif xmp.xmp_title:
            title = xmp.xmp_title

        # Description
        description = None
        if fitem.description:
            description = fitem.description
        elif xmp.xmp_description:
            description = xmp.xmp_description

        # Keywords
        # TODO(sthzg) check if overridden on item level
        tags = xmp.xmp_keywords.all()

        # Categories
        categories = fitem.filer_file.filemodelext_file.all()[0].category.all()

        # Stock links
        stock_items = fitem.filer_file.file_stocklinks.all()

        return render(
            request,
            t_settings['media'],
            {
                'base_extends': t_settings['base'],
                'fset': fset,
                'fitems': fitems,
                'set_type': set_type,
                'set_slug': set_slug,
                'media': fitem,
                'xmp': xmp,
                'title': title,
                'description': description,
                'tags': tags,
                'stock_items': stock_items,
                'categories': categories,
            }
        )



class ProcessSetView(View):
    def get(self, request, set_id=None):
        """
        Process a set with the given set_id

        Certain GET query parameters can be given:
        ?redirect=<url> If set, redirects to this url and sets a message

        :param set_id: pk of the set
        """
        try:
            fset = Set.objects.get(pk=int(set_id))
            op_stats = fset.create_or_update_set()
        except:
            # TODO Exception handling
            pass

        if 'redirect' in request.GET:
            msg = _('Processed set with id {}').format(set_id)
            messages.add_message(request, messages.SUCCESS, msg)
            return HttpResponseRedirect(request.GET['redirect'])

        # TODO  Work on the output
        return render(
            request,
            'filersets/process_set.html',
            {'op_stats': op_stats})


class CategoryMenuPartial(View):
    """Renders the category menu tree as HTML.

    This view can be utilized by backend code to get the rendered HTML
    for a category menu tree. For an implementation example see the
    ``fs_categorytree`` template tag.
    """
    def get(self, request, set_type_slug=None, root_id=-1, skip_empty=False):
        current_app = resolve(request.path).namespace

        if set_type_slug:
            set_type_inst = Settype.objects.get(slug=set_type_slug)
            template_conf = set_type_inst.template_conf
        else:
            try:
                # If we don't receive a set_type parameter with the slug we
                # try if the current app's namespace resolves to a set type.
                Settype.objects.get(template_conf=current_app)
                template_conf = current_app
            except Settype.DoesNotExist:
                template_conf = 'default'

        t_settings = get_template_settings(template_conf=template_conf)

        if root_id < 0:
            categories = Category.objects.get_categories_by_level(
                skip_empty=skip_empty)
            lvl_compensate = int(0)
        else:
            try:
                root_cat = Category.objects.get(pk=root_id)
                lvl_compensate = root_cat.get_level_compensation()
                categories = root_cat.get_descendants()
            except Category.DoesNotExist:
                # TODO Templatize the no categories display
                return _('<p>No categories available</p>')

        # Check back base system, see views.py for documentation
        fs_referrer = request.session.get('fs_referrer', None)
        back_base_url = request.session.get('back_base_url', None)
        has_back_base = request.session.get('has_back_base', False)

        litems = list()
        for cat in categories:
            cat_classes = list()
            cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))
            cat_set_type = cat.get_root().slug

            cat_slug_url = reverse(
                'filersets:list_view',
                kwargs=({'set_type': cat_set_type, 'cat_slug': cat.slug_composed}),
                current_app=cat_set_type)

            cat_id_url = reverse(
                'filersets:list_view',
                kwargs=({'set_type': cat_set_type, 'cat_id': cat.pk}),
                current_app=cat_set_type)

            cur_url = request.get_full_path()

            if cur_url in (cat_slug_url, cat_id_url):
                cat_classes.append('active')

            if has_back_base and back_base_url in (cat_slug_url, cat_id_url):
                # Prevent marking two cats as active when switching categories.
                if fs_referrer != '{}:list_view'.format(cat_set_type):
                    cat_classes.append('active')

            t = get_template(t_settings['cat_tree_item'])
            c = Context(
                {
                    'cat': cat,
                    'cat_classes': ' '.join(cat_classes),
                    'set_type': cat_set_type,
                    'current_app': current_app,
                }
            )

            litems.append(t.render(c))

        t = get_template(t_settings['cat_tree_wrap'])
        c = Context({
            'items': litems,
            'set_type': set_type_slug
        })

        return t.render(c)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows categories to be viewed."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ItemViewSet(viewsets.ModelViewSet):
    """API endpoint that allows categories to be viewed and modified."""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class FilemodelExtViewSet(viewsets.ModelViewSet):
    """API endpoint to view and modify filemodel extensions."""
    queryset = FilemodelExt.objects.all()
    serializer_class = FilemodelExtSerializer


class FileViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint to view and modify file model instances.."""
    queryset = File.objects.all()
    serializer_class = FileSerializer


class FilersetViewSet(viewsets.ModelViewSet):
    """API endpoint that allows retrieving filerset instances."""
    queryset = Set.objects.all()
    serializer_class = FilersetSerializer