from unittest import TestCase

from clean_fields.apps import CleanFieldsConfig


class CleanFieldsConfigTestCase(TestCase):
    def test_name_class_attr(self):
        self.assertEqual(CleanFieldsConfig.name, 'clean_fields')
