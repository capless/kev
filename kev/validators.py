import datetime
import time
import six

from .exceptions import ValidationException

__all__ = [
    "Validator",
    "RequiredValidator",
    "StringValidator",
    "IntegerValidator",
    "MaxValueValidator",
    "MinValueValidator",
    "MinLengthValidator",
    "MaxLengthValidator",
    "DateValidator",
    "DateTimeValidator",
    ]


class Validator(object):
        
    def validate(self,value,key):
        raise NotImplementedError


class RequiredValidator(Validator):
    
    def validate(self,value,key):
        if not value:
            raise ValidationException(
                '{0}: This value is required'.format(key)
                )


class StringValidator(Validator):
    
    def validate(self,value,key=None):
        if value and not isinstance(value, six.string_types):
            raise ValidationException(
                '{0}: This value should '
                'be a string'.format(key)
                )


class DateValidator(Validator):
    
    def validate(self, value,key=None):
        if value and isinstance(value,six.string_types):
            try:
                value = datetime.date(*time.strptime(value, '%Y-%m-%d')[:3])
            except ValueError:
                pass
        if value and not isinstance(value, datetime.date):
            raise ValidationException(
                '{0}: This value should be a valid date object.'.format(key))


class DateTimeValidator(Validator):
    
    def validate(self, value,key=None):
        if value and isinstance(value,six.string_types):
            try:
                value = value.split('.', 1)[0]  # strip out microseconds
                value = value[0:19]  # remove timezone
                value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except (IndexError,KeyError,ValueError):
                pass
        if value and not isinstance(value, datetime.datetime):
            raise ValidationException(
                '{0}: This value should be a valid datetime object.'.format(key))


class IntegerValidator(Validator):
    def validate(self,value,key=None):
        if value and not isinstance(value, int):
            raise ValidationException('{0}: This value should be an integer'.format(key))


class FloatValidator(Validator):
    def validate(self, value,key=None):
        if value and not isinstance(value, float):
            raise ValidationException('{0}: This value should be a float.'.format(key))


class MaxValueValidator(Validator):
    def __init__(self,compare_value):
        self.compare_value = compare_value
        
    def validate(self,value,key=None):
        if isinstance(value, (float,int)) and value > self.compare_value:
            raise ValidationException(
                '{0}: This value should '
                'have a value lesser than '
                '{1}. Currently {2}'.format(key,self.compare_value, value)
                )


class MinValueValidator(MaxValueValidator):
        
    def validate(self,value,key=None):
        if isinstance(value, (float,int)) and value < self.compare_value:
            raise ValidationException(
                '{0}: This value should '
                'have a value greater than '
                '{1}. Currently {2}'.format(key,self.compare_value, value)
                )


class MaxLengthValidator(Validator):
    
    def __init__(self,length):
        self.length = length
        
    def validate(self,value,key=None):
        if not isinstance(value, int) and len(value) > self.length:
            raise ValidationException(
                '{0}: This value should '
                'have a length lesser than '
                '{1}. Currently {2}'.format(key,self.length, value)
                )


class MinLengthValidator(MaxLengthValidator):
        
    def validate(self,value,key):
        if not isinstance(value, int) and len(value) < self.length:
            raise ValidationException(
                '{0}: This value should '
                'have a length greater than '
                '{1}. Currently {2}'.format(key,self.length, value)
                )


class BooleanValidator(Validator):

    def validate(self,value,key):
        try:
            int(value)
        except (TypeError,ValueError):
            raise ValidationException(
                '{0}: This value should be True or False.'.format(key)
            )
        if not isinstance(value,bool):
            raise ValidationException(
                '{0}: This value should be True or False.'.format(key)
            )