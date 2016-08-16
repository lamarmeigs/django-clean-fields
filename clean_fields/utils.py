from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class NoValue(object):
    """Empty class for disambiguating calls to getattr"""
    pass


def get_model_field_value(instance, field_name):
    """Retrieve the value of the named field from the given model instance.

    Args:
        instance: an instantiated model object
        field_name (str): the name of the field whose value to retrieve

    Raise:
        AttributeError: if no such field exists on the model instance
    """
    field_value = getattr(instance, field_name, NoValue)
    if field_value == NoValue:
        raise AttributeError(
            'Object {} has no field named "{}"'.format(instance, field_name)
        )
    return field_value


def get_model_field_names(instance):
    """Return names of all fields on model instance.

    In Django 1.8 and later, a model instance's `_meta` provides the
    `get_fields` method for retrieving field information. Prior versions must
    rely on `_meta`'s `get_all_field_names` method.

    Args:
        instance (django.db.models.Model): an instance of a registered model

    Return:
        list of str
    """
    try:
        field_names = [field.name for field in instance._meta.get_fields()]
    except AttributeError:
        field_names = instance._meta.get_all_field_names()
    return field_names


def parse_field_ref(field_ref):
    """Split a field reference into a model label and a field name.

    Args:
        field_ref (str): a label for the model field to clean, following the
            convention `app_name.ModelName.field_name`

    Return:
        2-tuple of str
    """
    app_name, model_name, field_name = field_ref.split('.')
    model_label = '.'.join([app_name, model_name])
    return model_label, field_name
