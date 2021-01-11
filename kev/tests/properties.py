import unittest
import datetime
from kev.properties import (BaseProperty, CharProperty, DateProperty,
                            DateTimeProperty, FloatProperty, IntegerProperty,
                            BooleanProperty, SlugProperty, EmailProperty)
from valley.exceptions import ValidationException


class PropertiesTestCase(unittest.TestCase):

    def test_base_property(self):
        prop = BaseProperty(required=True)
        self.assertEqual(None, prop.default_value)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'first_name')
        self.assertEqual(str(vm.exception),
                         'first_name: This value is required')

    def test_base_property_not_required(self):
        prop = BaseProperty(required=False)
        self.assertEqual(prop.required, False)
        prop.validate(None, 'first_name')

    def test_base_property_default_value(self):
        prop = BaseProperty(default_value=None)
        self.assertEqual(prop.get_default_value(), None)
        prop = BaseProperty(default_value='Redis')
        self.assertEqual(prop.get_default_value(), 'Redis')

    def test_char_property_validators_set(self):
        prop = CharProperty()
        self.assertEqual(1, len(prop.validators))
        propb = CharProperty(required=True,max_length=20,min_length=2)
        self.assertEqual(4, len(propb.validators))

    def test_char_property_validate(self):
        prop = CharProperty(required=True)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'first_name')
        self.assertEqual(str(vm.exception),
                         'first_name: This value is required')
        with self.assertRaises(ValidationException) as vm:
            prop.validate(34, 'first_name')
        self.assertEqual(str(vm.exception),
                         'first_name: This value should be a string')

    def test_char_property_validate_default_value(self):
        prop = CharProperty(required=True, default_value='Ben')
        # Make sure that the default value works
        prop.validate(None, 'first_name')
        self.assertEqual(prop.get_default_value(), 'Ben')
        prop = CharProperty(required=True, default_value=5)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'first_name')
        self.assertEqual(str(vm.exception),
                         'first_name: This value should be a string')

    def test_integer_property_validators_set(self):
        prop = IntegerProperty()
        self.assertEqual(1, len(prop.validators))
        propb = IntegerProperty(required=True)
        self.assertEqual(2, len(propb.validators))

    def test_integer_property_validate(self):
        prop = IntegerProperty(required=True)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value is required')
        with self.assertRaises(ValidationException) as vm:
            prop.validate('brains', 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value should be an integer')

    def test_integer_property_validate_default_value(self):
        prop = IntegerProperty(required=True, default_value=5)
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(prop.get_default_value(), 5)
        prop = IntegerProperty(required=True, default_value='Ben')
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value should be an integer')

    def test_float_property_validators_set(self):
        prop = FloatProperty()
        self.assertEqual(1, len(prop.validators))
        propb = FloatProperty(required=True)
        self.assertEqual(2, len(propb.validators))

    def test_float_property_validate(self):
        prop = FloatProperty(required=True)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value is required')
        with self.assertRaises(ValidationException) as vm:
            prop.validate('brains', 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value should be a float.')

    def test_float_property_validate_default_value(self):
        prop = FloatProperty(required=True, default_value=5.5)
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(prop.get_default_value(), 5.5)
        prop = FloatProperty(required=True, default_value=5)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value should be a float.')

    def test_date_property_validators_set(self):
        prop = DateProperty()
        self.assertEqual(2, len(prop.validators))

    def test_date_property_validate(self):
        prop = DateProperty(required=True)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value is required')
        with self.assertRaises(ValidationException) as vm:
            prop.validate('brains', 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value should be a valid date object.')

    def test_date_property_validate_auto_now(self):
        prop = DateProperty(required=True, auto_now=True)
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(prop.get_default_value(), datetime.date.today())

    def test_date_property_validate_auto_now_add(self):
        prop = DateProperty(required=True, auto_now_add=True)
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(prop.get_default_value(), datetime.date.today())

    def test_slug_property_validate(self):
        prop = SlugProperty(required=True)
        prop.validate('some-slug','slug')
        with self.assertRaises(ValidationException) as vm:
            prop.validate('sdfsd sfsdfsf','slug')
        self.assertEqual(str(vm.exception),
            'slug: This value should be a slug. ex. pooter-is-awesome')

    def test_email_property_validate(self):
        prop = EmailProperty(required=True)
        prop.validate('some@email.com','email')
        with self.assertRaises(ValidationException) as vm:
            prop.validate('some text','email')
        self.assertEqual(str(vm.exception),
            'email: This value should be a valid email address')

    def test_date_property_validate_default_value(self):
        prop = DateProperty(required=True, default_value=datetime.date.today())
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(prop.get_default_value(), datetime.date.today())

    def test_datetime_property_validate(self):
        prop = DateTimeProperty(required=True)
        with self.assertRaises(ValidationException) as vm:
            prop.validate(None, 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value is required')
        with self.assertRaises(ValidationException) as vm:
            prop.validate('brains', 'no_packages')
        self.assertEqual(str(vm.exception),
                         'no_packages: This value should be a valid datetime object.')

    def test_datetime_property_validate_default_value(self):
        prop = DateTimeProperty(
            required=True,
            default_value=datetime.datetime.now())
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(type(prop.get_default_value()), datetime.datetime)

    def test_datetime_property_validate_auto_now(self):
        prop = DateTimeProperty(requirYYed=True, auto_now=True)
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(type(prop.get_default_value()), datetime.datetime)

    def test_datetime_property_validate_auto_now_add(self):
        prop = DateTimeProperty(required=True, auto_now_add=True)
        # Make sure that the default value works
        prop.validate(None, 'no_packages')
        self.assertEqual(type(prop.get_default_value()), datetime.datetime)

    def test_boolean_property_validate(self):
        prop = BooleanProperty(required=True)
        with self.assertRaises(ValidationException) as vm:
            prop.validate('brains', 'is_staff')
        self.assertEqual(str(vm.exception),
                         'is_staff: This value should be True or False.')

    def test_boolean_property_validate_default_value(self):
        prop = BooleanProperty(default_value=True)
        # Make sure that the default value works
        prop.validate(None, 'is_active')
        self.assertEqual(type(prop.get_default_value()), type(True))


if __name__ == '__main__':
    unittest.main()
