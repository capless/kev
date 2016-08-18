import unittest
import datetime

from kev import (Document,CharProperty,DateTimeProperty,
                 DateProperty,BooleanProperty,IntegerProperty,
                 FloatProperty)
from kev.exceptions import ValidationException, QueryError
from kev.query import combine_list, combine_dicts
from kev.testcase import kev_handler,KevTestCase


class TestDocument(Document):
    name = CharProperty(required=True,unique=True,min_length=5,max_length=20)
    last_updated = DateTimeProperty(auto_now=True)
    date_created = DateProperty(auto_now_add=True)
    is_active = BooleanProperty(default_value=True)
    no_subscriptions = IntegerProperty(default_value=1,min_value=1,max_value=20)
    gpa = FloatProperty()

    def __unicode__(self):
        return self.name

    class Meta:
        use_db = 's3'
        handler = kev_handler


class BaseTestDocumentSlug(TestDocument):
    slug = CharProperty(required=True,unique=True)
    email = CharProperty(required=True,unique=True)
    city = CharProperty(required=True,index=True)


class S3TestDocumentSlug(BaseTestDocumentSlug):
    class Meta:
        use_db = 's3'
        handler = kev_handler


class RedisTestDocumentSlug(BaseTestDocumentSlug):
    class Meta:
        use_db = 'redis'
        handler = kev_handler


class DocumentTestCase(KevTestCase):

    def test_default_values(self):
        obj = TestDocument(name='Fred')
        self.assertEqual(obj.is_active,True)
        self.assertEqual(obj._doc.get('is_active'),True)
        self.assertEqual(obj.date_created,datetime.date.today())
        self.assertEqual(obj._doc.get('date_created'), datetime.date.today())
        self.assertEqual(type(obj.last_updated),datetime.datetime)
        self.assertEqual(type(obj._doc.get('last_updated')), datetime.datetime)
        self.assertEqual(obj.no_subscriptions,1)
        self.assertEqual(obj._doc.get('no_subscriptions'), 1)
        self.assertEqual(obj.gpa,None)
        self.assertFalse('gpa' in obj._doc)

    def test_get_unique_props(self):
        obj = S3TestDocumentSlug(name='Brian',slug='brian',email='brian@host.com',
                                 city='Greensboro',gpa=4.0)
        self.assertEqual(obj.get_unique_props().sort(),['name','slug','email'].sort())

    def test_set_indexed_prop(self):
        obj = S3TestDocumentSlug(name='Brian', slug='brian', email='brian@host.com',
                                 city='Greensboro', gpa=4.0)
        obj.name = 'Tariq'
        self.assertEqual(obj._index_change_list,['s3testdocumentslug:indexes:name:brian'])

    def test_validate_valid(self):
        t1 = TestDocument(name='DNSly',is_active=False,no_subscriptions=2,gpa=3.5)
        t1.save()

    def test_validate_boolean(self):
        t2 = TestDocument(name='Google', is_active='Gone', gpa=4.0)
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                          'is_active: This value should be True or False.')

    def test_validate_datetime(self):
        t2 = TestDocument(name='Google',gpa=4.0,last_updated='today')
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                          'last_updated: This value should be a valid datetime object.')

    def test_validate_date(self):
        t2 = TestDocument(name='Google', gpa=4.0, date_created='today')
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                          'date_created: This value should be a valid date object.')

    def test_validate_integer(self):
        t2 = TestDocument(name='Google', gpa=4.0, no_subscriptions='seven')
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                          'no_subscriptions: This value should be an integer')

    def test_validate_float(self):
        t2 = TestDocument(name='Google', gpa='seven')
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                          'gpa: This value should be a float.')

    def test_validate_unique(self):
        t1 = TestDocument(name='Google',gpa=4.0)
        t1.save()
        t2 = TestDocument(name='Google',gpa=4.0)
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                          'There is already a name with the value of Google')



class S3QueryTestCase(KevTestCase):

    doc_class = S3TestDocumentSlug

    def setUp(self):

        self.t1 = self.doc_class(name='Goo and Sons',slug='goo-sons',gpa=3.2,
                         email='goo@sons.com',city="Durham")
        self.t1.save()
        self.t2 = self.doc_class(name='Great Mountain', slug='great-mountain', gpa=3.2,
                                   email='great@mountain.com',city='Charlotte')
        self.t2.save()
        self.t3 = self.doc_class(name='Lakewoood YMCA', slug='lakewood-ymca', gpa=3.2,
                                   email='lakewood@ymca.com', city='Durham')
        self.t3.save()

    def test_non_unique_filter(self):
        qs = self.doc_class.objects().filter({'city':'durham'})
        self.assertEqual(2,qs.count())

    def test_objects_get_single_indexed_prop(self):
        obj = self.doc_class.objects().get({'name':self.t1.name})
        self.assertEqual(obj.slug,self.t1.slug)

    def test_get(self):
        obj = self.doc_class.get(self.t1.id)
        self.assertEqual(obj._id,self.t1._id)

    def test_flush_db(self):
        self.assertEqual(3,len(list(self.doc_class.all())))
        self.doc_class().flush_db()
        self.assertEqual(0, len(list(self.doc_class.all())))

    def test_delete(self):
        qs = self.doc_class.objects().filter({'city': 'durham'})
        self.assertEqual(2, qs.count())
        qs[0].delete()
        qs = self.doc_class.objects().filter({'city': 'durham'})
        self.assertEqual(1,qs.count())

    def test_queryset_iter(self):
        qs = self.doc_class.objects().filter({'city': 'durham'})
        for i in qs:
            self.assertIsNotNone(i.id)

    def test_queryset_chaininig(self):
        qs = self.doc_class.objects().filter(
            {'name':'Goo and Sons'}).filter({'city':'Durham'})
        self.assertEqual(1,qs.count())
        self.assertEqual(self.t1.name,qs[0].name)

    def test_objects_get_no_result(self):
        with self.assertRaises(QueryError) as vm:
            self.doc_class.objects().get({'username':'affsdfadsf'})
        self.assertEqual(str(vm.exception),
                          'This query did not return a result.')

    def test_all(self):
        qs = self.doc_class.all()
        self.assertEqual(3,len(list(qs)))

    def test_objects_get_multiple_results(self):
        with self.assertRaises(QueryError) as vm:
            self.doc_class.objects().get({'city': 'durham'})
        self.assertEqual(str(vm.exception),
            'This query should return exactly one result. Your query returned 2')

    def test_combine_list(self):
        a = [1,2,3]
        b = ['a','b','c']
        c = combine_list(a,b)
        self.assertEqual([1,2,3,'a','b','c'],c)

    def test_combine_dicts(self):
        a = {'username':'boywonder','doc_type':'goo'}
        b = {'email':'boywonder@superteam.com','doc_type':'foo'}
        c = combine_dicts(a,b)
        self.assertEqual({'username':'boywonder',
                          'email':'boywonder@superteam.com',
                          'doc_type':['goo','foo']},c)


class RedisQueryTestCase(S3QueryTestCase):

    doc_class = RedisTestDocumentSlug


if __name__ == '__main__':
    unittest.main()