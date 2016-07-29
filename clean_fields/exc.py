from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class CleanFieldsError(Exception):
    """Base error for exceptions raised in the clean_fields app."""
    pass


class CleanFieldsConfigurationError(CleanFieldsError):
    """Raised when a cleaner method is called for a field that doesn't exist"""
    def __init__(self, model_label, field_name, cleaner_name):
        message = (
            'Callable "{cleaner}" configured to clean "{field}", but '
            '"{model}" has no such field'.format(
                cleaner=cleaner_name,
                field=field_name,
                model=model_label
            )
        )
        return super(CleanFieldsConfigurationError, self).__init__(message)
