import unittest
import datetime
from kev.validators import (RequiredValidator,DateTimeValidator,
                            DateValidator,FloatValidator,IntegerValidator,
                            MaxLengthValidator,MinLengthValidator,
                            MaxValueValidator,MinValueValidator,
                            StringValidator,ValidationException,
                            BooleanValidator
                            )
from kev.document import Document
from kev.properties import CharProperty

class Frog(Document):
    name = CharProperty()


class Dog(Document):
    name = CharProperty()

    class Meta(object):
        doc_type = 'animal'


class ValidatorsTestCase(unittest.TestCase):

    def test_required_validator(self):
        with self.assertRaises(ValidationException) as vm:
            RequiredValidator().validate(None,'first_name')
        self.assertEqual(str(vm.exception), 'first_name: This value is required')
        #Test with valid input
        RequiredValidator().validate('First Name','first_name')

    def test_datetime_validator(self):
        with self.assertRaises(ValidationException) as vm:
            DateTimeValidator().validate(datetime.date.today(), 'date_created')
        self.assertEqual(str(vm.exception),
            'date_created: This value should be a valid datetime object.')
        # Test with valid input
        DateTimeValidator().validate(datetime.datetime.now(),'date_created')

    def test_date_validator(self):
        with self.assertRaises(ValidationException) as vm:
            DateValidator().validate('not a date', 'date_created')
        self.assertEqual(str(vm.exception),
                          'date_created: This value should be a valid date object.')
        # Test with valid input
        DateValidator().validate(datetime.date.today(),'date_created')

    def test_float_validator(self):
        with self.assertRaises(ValidationException) as vm:
            FloatValidator().validate(1, 'no_packages')
        self.assertEqual(str(vm.exception),
                          'no_packages: This value should be a float.')
        # Test with valid input
        FloatValidator().validate(1.3,'no_packages')

    def test_integer_validator(self):
        with self.assertRaises(ValidationException) as vm:
            IntegerValidator().validate(1.2, 'no_packages')
        self.assertEqual(str(vm.exception),
                          'no_packages: This value should be an integer')
        # Test with valid input
        IntegerValidator().validate(1, 'no_packages')

    def test_max_length_validator(self):
        with self.assertRaises(ValidationException) as vm:
            MaxLengthValidator(2).validate('123', 'no_packages')
        self.assertEqual(str(vm.exception),
            'no_packages: This value should have a length lesser than 2. Currently 123')
        # Test with valid input
        MaxLengthValidator(2).validate('12', 'no_packages')

    def test_min_length_validator(self):
        with self.assertRaises(ValidationException) as vm:
            MinLengthValidator(2).validate('1', 'no_packages')
        self.assertEqual(str(vm.exception),
            'no_packages: This value should have a length greater than 2. Currently 1')
        # Test with valid input
        MinLengthValidator(2).validate('123', 'no_packages')

    def test_max_value_validator(self):
        with self.assertRaises(ValidationException) as vm:
            MaxValueValidator(2).validate(3, 'no_packages')
        self.assertEqual(str(vm.exception),
            'no_packages: This value should have a value lesser than 2. Currently 3')
        # Test with valid input
        MaxValueValidator(2).validate(1, 'no_packages')

    def test_min_value_validator(self):
        with self.assertRaises(ValidationException) as vm:
            MinValueValidator(2).validate(1, 'no_packages')
        self.assertEqual(str(vm.exception),
                          'no_packages: This value should have a value greater than 2. Currently 1')
        # Test with valid input
        MinValueValidator(2).validate(3, 'no_packages')

    def test_string_validator(self):
        with self.assertRaises(ValidationException) as vm:
            StringValidator().validate(1, 'last_name')
        self.assertEqual(str(vm.exception),
                          'last_name: This value should be a string')
        # Test with valid input
        StringValidator().validate('Jones', 'last_name')

    def test_boolean_validator(self):
        with self.assertRaises(ValidationException) as vm:
            BooleanValidator().validate(1, 'last_name')
        self.assertEqual(str(vm.exception),
                          'last_name: This value should be True or False.')
        # Test with valid input
        BooleanValidator().validate(True, 'last_name')
        BooleanValidator().validate(False, 'last_name')

if __name__ == '__main__':
    unittest.main()