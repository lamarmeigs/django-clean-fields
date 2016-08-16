from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import TestCase

from django.db import models
from mock import patch

from clean_fields.utils import (
    get_model_field_value, get_model_field_names, parse_field_ref,
)


class GetModelFieldValueTestCase(TestCase):
    def test_model_has_no_field(self):
        class MissingFieldModel(models.Model):
            some_field = models.IntegerField()

        dummy = MissingFieldModel(some_field=5)
        with self.assertRaises(AttributeError) as ctx:
            get_model_field_value(dummy, 'not_a_field')
        self.assertEqual(
            str(ctx.exception),
            'Object {} has no field named "not_a_field"'.format(dummy)
        )

    def test_model_has_field(self):
        class HasFieldModel(models.Model):
            some_field = models.IntegerField()

        dummy = HasFieldModel(some_field=5)
        field_value = get_model_field_value(dummy, 'some_field')
        self.assertEqual(field_value, 5)


class GetModelFieldNamesTestCase(TestCase):
    def test_meta_has_get_field_method(self):
        class GetFieldModel(models.Model):
            some_field = models.IntegerField()

        class MockField(object):
            def __init__(self, name='test field'):
                self.name = name

        instance = GetFieldModel(some_field=5)
        instance._meta.get_fields = lambda x: x
        instance._meta.get_all_field_names = lambda x: x
        with patch.object(
            instance._meta,
            'get_fields',
            return_value=[MockField('id'), MockField('some_field')]
        ):
            field_names = get_model_field_names(instance)
        self.assertEqual(field_names, ['id', 'some_field'])

    def test_meta_has_no_get_field_method(self):
        class GetAllFieldNameModel(models.Model):
            some_field = models.IntegerField()

        instance = GetAllFieldNameModel(some_field=5)
        instance._meta.get_fields = lambda x: x
        instance._meta.get_all_field_names = lambda x: x
        with patch.object(
            instance._meta,
            'get_fields',
            side_effect=AttributeError()
        ):
            with patch.object(
                instance._meta,
                'get_all_field_names',
                return_value=['id', 'some_field']
            ):
                field_names = get_model_field_names(instance)
        self.assertEqual(field_names, ['id', 'some_field'])


class ParseFieldRefTestCase(TestCase):
    def test_parsed_model_label(self):
        model_label, _ = parse_field_ref('app_name.ModelName.field_name')
        self.assertEqual(model_label, 'app_name.ModelName')

    def test_parsed_field_name(self):
        _, field_name = parse_field_ref('app_name.ModelName.field_name')
        self.assertEqual(field_name, 'field_name')
