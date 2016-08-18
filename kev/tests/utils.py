import unittest

from kev.utils import import_util, import_mod, get_doc_type
from kev.document import Document
from kev.properties import CharProperty

class Frog(Document):
    name = CharProperty()


class Dog(Document):
    name = CharProperty()

    class Meta(object):
        doc_type = 'animal'


class UtilTest(unittest.TestCase):

    def test_import_util(self):
        klass = import_util('kev.backends.s3.db.S3DB')
        self.assertEqual('S3DB',klass.__name__)

    def test_import_mod(self):
        mod = import_mod('kev.backends.s3.db')
        self.assertTrue(hasattr(mod,'S3DB'))

    def test_get_doc_type(self):
        a = get_doc_type(Frog)
        self.assertEqual('Frog',a)
        b = get_doc_type(Dog)
        self.assertEqual('animal', b)

if __name__ == '__main__':
    unittest.main()