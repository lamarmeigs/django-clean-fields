from unittest import TestCase

from django.db import models
from django.db.models.signals import pre_save
from mock import Mock, patch

from clean_fields.decorators import cleans_field
from clean_fields.exc import CleanFieldsConfigurationError


class CleansFieldTestCase(TestCase):
    def test_pre_save_signal_handler_registered(self):
        with patch.object(pre_save, 'connect') as mock_connect:
            cleans_field('app_name.ModelName.field_name')(lambda x: x)
        self.assertEqual(mock_connect.call_count, 1)

    def test_signal_handler_raises_error_on_incorrect_field(self):
        class BadFieldModel(models.Model):
            some_field = models.IntegerField()

            @cleans_field('clean_fields.BadFieldModel.not_a_field')
            def clean_some_field(self, some_field):
                return some_field + 1

        dummy = BadFieldModel(some_field=5)
        with self.assertRaises(CleanFieldsConfigurationError):
            pre_save.send(dummy.__class__, instance=dummy)

    def test_signal_handler_raises_no_error_on_empty_field(self):
        class GoodFieldModel(models.Model):
            some_field = models.IntegerField()

            @cleans_field('clean_fields.GoodFieldModel.some_field')
            def clean_some_field(self, some_field):
                return some_field + 1

        dummy = GoodFieldModel(some_field=5)
        try:
            pre_save.send(dummy.__class__, instance=dummy)
        except Exception as error:
            self.fail(
                'Sending pre_save signal resulted in unexpected error:\n\t'
                '{error}'.format(error=str(error))
            )

    def test_returns_cleaner_executor(self):
        """Ensures decorated callables can still be invoked independently"""
        cleaner_function = Mock()
        wrap_function = cleans_field('app_name.ModelName.field_name')
        wrapped_function = wrap_function(cleaner_function)
        wrapped_function(1, 2, 'foobar')
        cleaner_function.assert_called_once_with(1, 2, 'foobar')
