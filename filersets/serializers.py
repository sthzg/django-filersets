# -*- coding: utf-8 -*-
from filersets.models import Category, Item, FilemodelExt
from filer.models import File
from rest_framework import serializers


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug_composed')


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'title', 'category',)


class FileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = File
        fields = ('id',)


class FilemodelExtSerializer(serializers.HyperlinkedModelSerializer):
    filer_file = serializers.HyperlinkedRelatedField(view_name='file-detail')
    tags = serializers.Field(source='get_tags_display')

    class Meta:
        model = FilemodelExt
        fields = ('filer_file', 'is_timeline', 'category', 'tags',)