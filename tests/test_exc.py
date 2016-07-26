from unittest import TestCase

from clean_fields.exc import CleanFieldsError, CleanFieldsConfigurationError


class CleanFieldsErrorTestCase(TestCase):
    def test_inheritance(self):
        error = CleanFieldsError()
        self.assertIsInstance(error, Exception)


class CleanFieldsConfigurationErrorTestCase(TestCase):
    def test_inheritance(self):
        error = CleanFieldsConfigurationError('app.Model', 'field', 'cleaner')
        self.assertIsInstance(error, CleanFieldsError)

    def test_message(self):
        error = CleanFieldsConfigurationError(
            'app_name.ModelName',
            'field_name',
            'clean_field_name'
        )
        self.assertIn(
            'Callable "clean_field_name" configured to clean "field_name", '
            'but "app_name.ModelName" has no such field',
            str(error)
        )
