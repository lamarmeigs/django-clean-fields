from django.db.models import Model

# TODO: field cleaners should be definable anywhere, and not have any
# restrictions on naming. Perhaps create an external registry?


class CleanFieldsModel(Model):
    """Represents a base model that calls registered field cleaners on save.

    This class enables the use of special field cleaning methods which will be
    run every time `save` is called. These methods should accept the current
    value of the field, return a cleaned value (or raise an error), and adhere
    to the name convention `clean_{field_name}`.
    """

    def save(self, *args, **kwargs):
        """Call registered field cleaner methods before saving."""
        field_names = [field.name for field in self._meta.get_fields()]
        for field_name in field_names:
            field_cleaner = getattr(self, 'clean_{}'.format(field_name), None)
            if field_cleaner and callable(field_cleaner):
                field_value = getattr(self, field_name)
                setattr(self, field_name, field_cleaner(field_value))
        return super(CleanFieldsModel, self).save(*args, **kwargs)
