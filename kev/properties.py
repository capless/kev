"""
Redis document property classes. Much of the date and time property
code was borrowed or inspired by Benoit Chesneau's CouchDBKit library.
"""

from valley.mixins import CharVariableMixin, IntegerVariableMixin, \
    FloatVariableMixin, SlugVariableMixin, \
    EmailVariableMixin, BooleanMixin, DateMixin, DateTimeMixin
from valley.properties import BaseProperty as VBaseProperty


class BaseProperty(VBaseProperty):

    def __init__(
        self,
        default_value=None,
        required=False,
        index=False,
        unique=False,
        validators=[],
        verbose_name=None,
        **kwargs
    ):
        super(BaseProperty, self).__init__(default_value=default_value,
                                           required=required,
                                           validators=validators,
                                           verbose_name=verbose_name,
                                           **kwargs)
        self.index = index
        self.unique = unique
        if unique:
            self.index = True


class CharProperty(CharVariableMixin,BaseProperty):
    pass


class SlugProperty(SlugVariableMixin,BaseProperty):
    pass


class EmailProperty(EmailVariableMixin,BaseProperty):
    pass


class IntegerProperty(IntegerVariableMixin, BaseProperty):
    pass


class FloatProperty(FloatVariableMixin, BaseProperty):
    pass


class BooleanProperty(BooleanMixin, BaseProperty):

    def get_db_value(self, value):
        return int(value)


class DateProperty(DateMixin, BaseProperty):

    def __init__(
            self,
            default_value=None,
            required=True,
            validators=[],
            verbose_name=None,
            auto_now=False,
            auto_now_add=False,
            **kwargs):

        super(
            DateProperty,
            self).__init__(
            default_value=default_value,
            required=required,
            validators=validators,
            verbose_name=verbose_name,
            **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add


class DateTimeProperty(DateTimeMixin, BaseProperty):

    def __init__(
            self,
            default_value=None,
            required=True,
            validators=[],
            verbose_name=None,
            auto_now=False,
            auto_now_add=False,
            **kwargs):

        super(
            DateTimeProperty,
            self).__init__(
            default_value=default_value,
            required=required,
            validators=validators,
            verbose_name=verbose_name,
            **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
