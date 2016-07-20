from unittest import TestCase

from django.db import models
from mock import patch

from clean_fields.models import CleanFieldsModel


class CleanFieldsModelTestCase(TestCase):
    @patch('django.db.models.Model.save')
    def test_save_without_cleaner(self, mock_save):
        class DummyModel(CleanFieldsModel):
            some_field = models.IntegerField()

        dummy = DummyModel(some_field=5)
        dummy.save()

    @patch('django.db.models.Model.save')
    def test_save_with_uncallable_cleaner(self, mock_save):
        class DummyModel(CleanFieldsModel):
            some_field = models.IntegerField()
            clean_some_field = 'not callable'

        dummy = DummyModel(some_field=5)
        dummy.save()

    @patch('django.db.models.Model.save')
    def test_save_with_cleaner(self, mock_save):
        class DummyModel(CleanFieldsModel):
            some_field = models.IntegerField()

            def clean_some_field(self, some_field):
                return 42

        dummy = DummyModel(some_field=5)
        dummy.save()
        self.assertEqual(dummy.some_field, 42)
