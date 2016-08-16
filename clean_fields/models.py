from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db.models import Model

from clean_fields.utils import get_model_field_names


class BaseCleanFieldsModel(Model):
    """Represents a base model that calls registered field cleaners on save.

    This abstract base model provides the ability to invoke methods that clean
    field values on save. Such methods should accept the current value of the
    field and return a finalized value to commit to the database (or raise an
    error).

    This class should not be inherited directly. It does not provide a
    strategy to locate the cleaner methods; this feature is provided by
    child classes that implement the `_get_field_cleaner` method.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Call cleaners for each field before saving."""
        self.clean_single_fields()
        return super(BaseCleanFieldsModel, self).save(*args, **kwargs)

    def clean_single_fields(self):
        """Locate and invoke cleaner methods for each individial field."""
        field_names = get_model_field_names(self)
        for field_name in field_names:
            field_cleaner = self._get_field_cleaner(field_name)
            if field_cleaner:
                setattr(self, field_name, field_cleaner())

    def _get_field_cleaner(self, field_name):
        """Locate field cleaner callables for field with the given name.

        Args:
            field_name (str): name of the field on this model whose cleaners
                to retrieve.

        Return:
            callable or None
        """
        raise NotImplementedError()


class CleanFieldsModel(BaseCleanFieldsModel):
    """An abstract model to support the use of specially-named cleaner methods.

    This class locates cleaner methods by name, expecting them to exist on the
    same model and adhere to the naming convention `clean_{field_name}`.
    """
    class Meta:
        abstract = True

    def _get_field_cleaner(self, field_name):
        """Return any cleaners for the named field.

        Args:
            field_name (str): name of the field on this model whose cleaners
                to retrieve.

        Return:
            callable or None
        """
        field_cleaner = getattr(self, 'clean_{}'.format(field_name), None)
        if field_cleaner and not callable(field_cleaner):
            field_cleaner = None
        return field_cleaner
