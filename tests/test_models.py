from unittest import TestCase

from django.db import models
from mock import patch

from clean_fields.models import BaseCleanFieldsModel, CleanFieldsModel


class BaseCleanFieldsModelTestCase(TestCase):
    def test_get_field_cleaner_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            BaseCleanFieldsModel()._get_field_cleaner('field_name')

    @patch('django.db.models.Model.save')
    def test_save_without_cleaner(self, mock_save):
        class CleanerlessBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleanerlessBaseModel(some_field=5)
        with patch.object(dummy, '_get_field_cleaner', return_value=None):
            dummy.save()
        self.assertEqual(dummy.some_field, 5)

    @patch('django.db.models.Model.save')
    def test_save_with_cleaner(self, mock_save):
        class CleaningBaseModel(BaseCleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleaningBaseModel(some_field=5)
        with patch.object(
            dummy,
            '_get_field_cleaner',
            return_value=lambda x: 42
        ):
            dummy.save()
        self.assertEqual(dummy.some_field, 42)


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

            def clean_some_field(self, some_field):
                return 42

        dummy = CleaningNaiveModel(some_field=5)
        self.assertEqual(
            dummy._get_field_cleaner('some_field'),
            dummy.clean_some_field
        )
