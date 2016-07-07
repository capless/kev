"""
Redis document property classes. Much of the date and time property
code was borrowed or inspired by Benoit Chesneau's CouchDBKit library.
"""

import datetime
import time

from decimal import Decimal

from .validators import (RequiredValidator,StringValidator,
                         MaxLengthValidator,MinLengthValidator,
                         IntegerValidator,MaxValueValidator,
                         MinValueValidator,FloatValidator,
                         DateValidator,DateTimeValidator,
                         )

class VariableMixin(object):
    def get_validators(self):
        if self.required:
            self.validators.insert(0,RequiredValidator())
    
class CharVariableMixin(VariableMixin):
    
    def get_validators(self):
        VariableMixin.get_validators(self)
        self.validators.append(StringValidator())
        if self.kwargs.get('min_length'):
            self.validators.append(MaxLengthValidator(
                self.kwargs.get('min_length')))
            
        if self.kwargs.get('max_length'):
            self.validators.append(MinLengthValidator(
                self.kwargs.get('max_length')))
        
class NumericVariableMixin(VariableMixin):    
    def get_validators(self):
        VariableMixin.get_validators(self)
        if self.kwargs.get('max_value'):
            self.validators.append(MaxValueValidator(
                self.kwargs.get('max_value')))
            
        if self.kwargs.get('min_value'):
            self.validators.append(MinValueValidator(
                self.kwargs.get('min_value')))
            
class IntegerVariableMixin(NumericVariableMixin):
    
    def get_validators(self):
        super(IntegerVariableMixin,self).get_validators()
        self.validators.insert(0,IntegerValidator())
            
class FloatVariableMixin(NumericVariableMixin):
    
    def get_validators(self):
        super(FloatVariableMixin,self).get_validators()
        self.validators.insert(0, FloatValidator())

      
class DateMixin(VariableMixin):
    
    def get_validators(self):
        super(DateMixin,self).get_validators()
        self.validators.insert(0,DateValidator())
        
class DateTimeMixin(VariableMixin):
    
    def get_validators(self):
        super(DateTimeMixin,self).get_validators()
        self.validators.insert(0,DateTimeValidator())
        

class BaseProperty(object):
    
    def __init__(
        self,
        default_value=None,
        required=True,
        index=False,
        validators=[],
        verbose_name=None,
        **kwargs
        ):
        self.default_value = default_value
        self.required = required
        self.index = index
        self.kwargs = kwargs
        self.validators = list()
        self.get_validators()
        
        if verbose_name:
            self.verbose_name = verbose_name
            
    def validate(self,value,key):
        for i in self.validators:
            i.validate(value,key)
            
    def get_default_value(self):
        """ return default value """

        default = self.default_value
        if callable(default):
            default = default()
        return default
    
    def get_db_value(self,value):
        return value
    
    def get_python_value(self,value):
        return value
    
class CharProperty(CharVariableMixin,BaseProperty):
    
    def get_db_value(self, value):
        return unicode(value)
    
    def get_python_value(self, value):
        return unicode(value)

class IntegerProperty(IntegerVariableMixin,BaseProperty):
    
    def get_db_value(self, value):
        return int(value)
    
    def get_python_value(self, value):
        return int(value)
    
    
class FloatProperty(FloatVariableMixin,BaseProperty):
    
    def get_db_value(self, value):
        return float(value)
    
    def get_python_value(self, value):
        return float(value)
    
class DateProperty(DateMixin,BaseProperty):

    def __init__(
        self, 
        default_value=None, 
        required=True, 
        validators=[], 
        verbose_name=None, 
        auto_now=False,
        auto_now_add=False,
        **kwargs):
        
        super(DateProperty,self).__init__(default_value=default_value,
                required=required, validators=validators, 
                verbose_name=verbose_name, **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
                
    def now(self):
        return datetime.datetime.now().date()
    
    def get_default_value(self):
        default = self.default_value
        if self.auto_now or self.auto_now_add:
            return self.now()
        return default
    
    def get_python_value(self, value):
        if isinstance(value, basestring):
            try:
                value = datetime.date(*time.strptime(value, '%Y-%m-%d')[:3])
            except ValueError, e:
                raise ValueError('Invalid ISO date %r [%s]' % (value,
                    str(e)))
        return value

    def get_db_value(self, value):
        if value is None:
            return value
        return value.isoformat()
    
class DateTimeProperty(DateTimeMixin,DateProperty):
    
    def get_python_value(self, value):
        if isinstance(value, basestring):
            try:
                value = value.split('.', 1)[0] # strip out microseconds
                value = value[0:19] # remove timezone
                value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except ValueError, e:
                raise ValueError('Invalid ISO date/time %r [%s]' %
                        (value, str(e)))
        return value

    def get_db_value(self, value):
        if self.auto_now:
            value = self.now()

        if value is None:
            return value
        return value.replace(microsecond=0).isoformat() + 'Z'
    
    def now(self):
        return datetime.datetime.utcnow()



    