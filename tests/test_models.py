from unittest import TestCase

from django.db import models
from mock import patch

from clean_fields.models import CleanFieldsModel


class CleanFieldsModelTestCase(TestCase):
    @patch('django.db.models.Model.save')
    def test_save_without_cleaner(self, mock_save):
        class CleanerlessModel(CleanFieldsModel):
            some_field = models.IntegerField()

        dummy = CleanerlessModel(some_field=5)
        dummy.save()

    @patch('django.db.models.Model.save')
    def test_save_with_uncallable_cleaner(self, mock_save):
        class UncallableCleanerModel(CleanFieldsModel):
            some_field = models.IntegerField()
            clean_some_field = 'not callable'

        dummy = UncallableCleanerModel(some_field=5)
        dummy.save()

    @patch('django.db.models.Model.save')
    def test_save_with_cleaner(self, mock_save):
        class CleaningModel(CleanFieldsModel):
            some_field = models.IntegerField()

            def clean_some_field(self, some_field):
                return 42

        dummy = CleaningModel(some_field=5)
        dummy.save()
        self.assertEqual(dummy.some_field, 42)
