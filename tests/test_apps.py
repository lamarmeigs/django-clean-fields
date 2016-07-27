from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import TestCase

from clean_fields.apps import CleanFieldsConfig


class CleanFieldsConfigTestCase(TestCase):
    def test_name_class_attr(self):
        self.assertEqual(CleanFieldsConfig.name, 'clean_fields')
