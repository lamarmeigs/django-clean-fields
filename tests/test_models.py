from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import TestCase

from django.db import models
from mock import patch

from clean_fields.models import (
    BaseCleanFieldsModel, CleanFieldsModel, ValidationMixin
)


class BaseCleanFieldsModelTestCase(TestCase):
    def test_get_field_cleaner_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            BaseCleanFieldsModel()._get_field_cleaner('field_name')

    @patch('django.db.models.Model.save')
    def test_save_invokes_clean_single_fields(self, mock_save):
        class SaveableBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = SaveableBaseModel(some_field=5)
        with patch.object(dummy, 'clean_single_fields') as mock_clean_fields:
            dummy.save()
        mock_clean_fields.assert_called_once_with()
        mock_save.assert_called_once_with()

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


class ValidationMixinTestCase(TestCase):
    @patch('django.db.models.Model.clean')
    def test_no_clean_on_validate(self, mock_clean):
        class NoValidationModel(ValidationMixin, BaseCleanFieldsModel):
            clean_on_validate = False

        dummy = NoValidationModel()
        with patch.object(dummy, 'clean_single_fields') as mock_clean_fields:
            dummy.clean()
        mock_clean_fields.assert_not_called()
        mock_clean.assert_called_once_with()

    def test_clean_on_validate(self):
        class ValidationModel(ValidationMixin, BaseCleanFieldsModel):
            clean_on_validate = True

        dummy = ValidationModel()
        with patch.object(dummy, 'clean_single_fields') as mock_clean_fields:
            with patch('django.db.models.Model.clean') as mock_clean:
                dummy.clean()
        mock_clean_fields.assert_called_once_with()
        mock_clean.assert_called_once_with()


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
