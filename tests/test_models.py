from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import TestCase

from django.db import models
from mock import patch

from clean_fields.models import (
    BaseCleanFieldsModel, CleanFieldsModel, get_model_field_names
)


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


class BaseCleanFieldsModelTestCase(TestCase):
    def test_get_field_cleaner_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            BaseCleanFieldsModel()._get_field_cleaner('field_name')

    @patch('django.db.models.Model.save')
    def test_save_invokes_scrub_fields(self, mock_save):
        class SaveableBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = SaveableBaseModel(some_field=5)
        with patch.object(dummy, 'scrub_fields') as mock_scrub_fields:
            dummy.save()
        mock_scrub_fields.assert_called_once_with()
        mock_save.assert_called_once_with()

    def test_scrub_fields_delegation(self):
        class ScrubFieldsBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = ScrubFieldsBaseModel(some_field=5)
        with patch.object(dummy, 'clean_single_fields') as mock_clean_single:
            with patch.object(dummy, 'clean_multiple_fields') as mock_multiple:
                dummy.scrub_fields()
        mock_clean_single.assert_called_once_with()
        mock_multiple.assert_called_once_with()

    def test_clean_single_fields_without_cleaner(self):
        class CleanerlessBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleanerlessBaseModel(some_field=5)
        with patch.object(dummy, '_get_field_cleaner', return_value=None):
            dummy.clean_single_fields()
        self.assertEqual(dummy.some_field, 5)

    def test_clean_single_fields_with_cleaner(self):
        class CleaningBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleaningBaseModel(some_field=5)
        with patch.object(
            dummy,
            '_get_field_cleaner',
            return_value=lambda: 42
        ):
            dummy.clean_single_fields()
        self.assertEqual(dummy.some_field, 42)

    def test_clean_multiple_fields_has_no_effect(self):
        class CleanerlessMultipleBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleanerlessMultipleBaseModel(some_field=5)
        dummy.clean_multiple_fields()
        self.assertEqual(dummy.some_field, 5)


class CleanFieldsModelTestCase(TestCase):
    def test_get_find_cleaner_with_missing_cleaner(self):
        class CleanerlessNaiveModel(CleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleanerlessNaiveModel(some_field=5)
        self.assertIsNone(dummy._get_field_cleaner('some_field'))

    def test_get_find_cleaner_with_uncallable_cleaner(self):
        class UncallableCleanerNaiveModel(CleanFieldsModel):
            some_field = models.IntegerField()
            clean_some_field = 'not callable'

        dummy = UncallableCleanerNaiveModel(some_field=5)
        self.assertIsNone(dummy._get_field_cleaner('some_field'))

    def test_get_find_cleaner_returns_cleaner(self):
        class CleaningNaiveModel(CleanFieldsModel):
            some_field = models.IntegerField()

            def clean_some_field(self):
                return 42

        dummy = CleaningNaiveModel(some_field=5)
        self.assertEqual(
            dummy._get_field_cleaner('some_field'),
            dummy.clean_some_field
        )
