import datetime

from exceptions import ValidationException

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
    
    def validate(self,value,key=None):
        if not value:
            raise ValidationException(
                u'{0}: This value is required'.format(key)
                )


class StringValidator(Validator):
    
    def validate(self,value,key=None):
        if value and not isinstance(value, (unicode,str)):
            raise ValidationException(
                u'{0}: This value should '
                'be a string'.format(key)
                )


class DateValidator(Validator):
    
    def validate(self, value,key=None):
        if value and not isinstance(value, datetime.date):
            raise ValidationException(
                u'{0}: This value should be a valid date object.'.format(key))
        
class DateTimeValidator(Validator):
    
    def validate(self, value,key=None):
        if value and not isinstance(value, datetime.datetime):
            raise ValidationException(
                u'{0}: This value should be a valid datetime object.'.format(key))
        
class IntegerValidator(Validator):
    def validate(self,value,key=None):
        if value and not isinstance(value, int):
            raise ValidationException(u'{0}: This value should be an integer'.format(key))
      
class FloatValidator(Validator):
    def validate(self, value,key=None):
        if value and not isinstance(value, float):
            raise ValidationException(u'{0}: This value should be a float.'.format(key))
              
class MaxValueValidator(Validator):
    def __init__(self,compare_value):
        self.compare_value = compare_value
        
    def validate(self,value,key=None):
        if not isinstance(value, int) and value > self.compare_value:
            raise ValidationException(
                u'{0}: This value should '
                'have a value lesser than '
                '{1}. Currently {2}'.format(key,self.compare_value, value)
                )

class MinValueValidator(MaxValueValidator):
        
    def validate(self,value,key=None):
        if not isinstance(value, int) and value < self.compare_value:
            raise ValidationException(
                u'{0}: This value should '
                'have a value greater than '
                '{1}. Currently {2}'.format(key,self.compare_value, value)
                )

class MaxLengthValidator(Validator):
    
    def __init__(self,length):
        self.length = length
        
    def validate(self,value,key=None):
        if not isinstance(value, int) and len(value) > self.length:
            raise ValidationException(
                u'{0}: This value should '
                'have a length lesser than '
                '{1}. Currently {2}'.format(key,self.length, value)
                )

class MinLengthValidator(MaxLengthValidator):
        
    def validate(self,value,key):
        if not isinstance(value, int) and value < self.length:
            raise ValidationException(
                u'{0}: This value should '
                'have a length greater than '
                '{1}. Currently {2}'.format(key,self.length, value)
                )