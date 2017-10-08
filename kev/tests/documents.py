import json
import os
import unittest
import datetime
import time

from botocore.exceptions import ClientError
from envs import env

from kev import (Document,CharProperty,DateTimeProperty,
                 DateProperty,BooleanProperty,IntegerProperty,
                 FloatProperty)
from kev.exceptions import QueryError
from kev.query import combine_list, combine_dicts
from kev.testcase import kev_handler,KevTestCase
from valley.exceptions import ValidationException


class TestDocument(Document):
    name = CharProperty(
        required=True,
        unique=True,
        min_length=5,
        max_length=20)
    last_updated = DateTimeProperty(auto_now=True)
    date_created = DateProperty(auto_now_add=True)
    is_active = BooleanProperty(default_value=True)
    no_subscriptions = IntegerProperty(
        default_value=1, min_value=1, max_value=20)
    gpa = FloatProperty()

    def __unicode__(self):
        return self.name

    class Meta:
        use_db = 's3redis'
        handler = kev_handler


class BaseTestDocumentSlug(TestDocument):
    slug = CharProperty(required=True, unique=True)
    email = CharProperty(required=True, unique=True)
    city = CharProperty(required=True, index=True)

class S3TestDocumentSlug(BaseTestDocumentSlug):

    class Meta:
        use_db = 's3'
        handler = kev_handler

class S3RedisTestDocumentSlug(BaseTestDocumentSlug):
    class Meta:
        use_db = 's3redis'
        handler = kev_handler


class RedisTestDocumentSlug(BaseTestDocumentSlug):

    class Meta:
        use_db = 'redis'
        handler = kev_handler


class DocumentTestCase(KevTestCase):

    def test_default_values(self):
        obj = TestDocument(name='Fred')
        self.assertEqual(obj.is_active, True)
        self.assertEqual(obj._data.get('is_active'), True)
        self.assertEqual(obj.date_created, datetime.date.today())
        self.assertEqual(obj._data.get('date_created'), datetime.date.today())
        self.assertEqual(type(obj.last_updated), datetime.datetime)
        self.assertEqual(type(obj._data.get('last_updated')), datetime.datetime)
        self.assertEqual(obj.no_subscriptions, 1)
        self.assertEqual(obj._data.get('no_subscriptions'), 1)
        self.assertEqual(obj.gpa,None)


    def test_get_unique_props(self):
        obj = S3RedisTestDocumentSlug(name='Brian',slug='brian',email='brian@host.com',
                                 city='Greensboro',gpa=4.0)
        self.assertEqual(obj.get_unique_props().sort(),['name','slug','email'].sort())

    def test_set_indexed_prop(self):
        obj = S3RedisTestDocumentSlug(name='Brian', slug='brian', email='brian@host.com',
                                 city='Greensboro', gpa=4.0)
        obj.name = 'Tariq'
        self.assertEqual(obj._index_change_list,['s3redis:s3redistestdocumentslug:indexes:name:brian'])

    def test_validate_valid(self):
        t1 = TestDocument(
            name='DNSly',
            is_active=False,
            no_subscriptions=2,
            gpa=3.5)
        t1.save()

    def test_validate_boolean(self):
        t2 = TestDocument(name='Google', is_active='Gone', gpa=4.0)
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                         'is_active: This value should be True or False.')

    def test_validate_datetime(self):
        t2 = TestDocument(name='Google', gpa=4.0, last_updated='today')
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
        t1 = TestDocument(name='Google', gpa=4.0)
        t1.save()
        t2 = TestDocument(name='Google', gpa=4.0)
        with self.assertRaises(ValidationException) as vm:
            t2.save()
        self.assertEqual(str(vm.exception),
                         'There is already a name with the value of Google')



class S3RedisQueryTestCase(KevTestCase):

    doc_class = S3RedisTestDocumentSlug

    def setUp(self):
        self.t1 = self.doc_class(name='Goo and Sons', slug='goo-sons', gpa=3.0,
                                 email='goo@sons.com', city="Durham")
        self.t1.save()
        self.t2 = self.doc_class(
            name='Great Mountain', slug='great-mountain',
            gpa=3.1, email='great@mountain.com', city='Charlotte')
        self.t2.save()
        self.t3 = self.doc_class(
            name='Lakewoood YMCA', slug='lakewood-ymca', gpa=3.2,
            email='lakewood@ymca.com', city='Durham')
        self.t3.save()

    def test_non_unique_filter(self):
        qs = self.doc_class.objects().filter({'city': 'durham'})
        self.assertEqual(2, qs.count())

    def test_non_unique_wildcard_filter(self):
        qs = self.doc_class.objects().filter({'city': 'du*ham'})
        self.assertEqual(2, qs.count())

    def test_objects_get_single_indexed_prop(self):
        obj = self.doc_class.objects().get({'name': self.t1.name})
        self.assertEqual(obj.slug, self.t1.slug)

    def test_get(self):
        obj = self.doc_class.get(self.t1.id)
        self.assertEqual(obj._id, self.t1._id)

    def test_flush_db(self):
        self.assertEqual(3, len(list(self.doc_class.all())))
        self.doc_class().flush_db()
        self.assertEqual(0, len(list(self.doc_class.all())))

    def test_delete(self):
        qs = self.doc_class.objects().filter({'city': 'durham'})
        self.assertEqual(2, qs.count())
        qs[0].delete()
        qs = self.doc_class.objects().filter({'city': 'durham'})
        self.assertEqual(1, qs.count())

    def test_wildcard_queryset_iter(self):
        qs = self.doc_class.objects().filter({'city': 'du*ham'})
        for i in qs:
            self.assertIsNotNone(i.id)

    def test_queryset_iter(self):
        qs = self.doc_class.objects().filter({'city': 'durham'})
        for i in qs:
            self.assertIsNotNone(i.id)

    def test_wildcard_queryset_chaining(self):
        qs = self.doc_class.objects().filter(
            {'name': 'Goo*'}).filter({'city': 'Du*ham'})
        self.assertEqual(1, qs.count())
        self.assertEqual(self.t1.name, qs[0].name)

    def test_queryset_chaining(self):
        qs = self.doc_class.objects().filter(
            {'name': 'Goo and Sons'}).filter({'city': 'Durham'})
        self.assertEqual(1, qs.count())
        self.assertEqual(self.t1.name, qs[0].name)

    def test_objects_get_no_result(self):
        with self.assertRaises(QueryError) as vm:
            self.doc_class.objects().get({'username': 'affsdfadsf'})
        self.assertEqual(str(vm.exception),
                         'This query did not return a result.')

    def test_objects_wildcard_get_no_result(self):
        with self.assertRaises(QueryError) as vm:
            self.doc_class.objects().get({'username': 'affsd*adsf'})
        self.assertEqual(str(vm.exception),
                         'This query did not return a result.')

    def test_all(self):
        qs = self.doc_class.all()
        self.assertEqual(3, len(list(qs)))

    def test_objects_get_multiple_results(self):
        with self.assertRaises(QueryError) as vm:
            self.doc_class.objects().get({'city': 'durham'})
        self.assertEqual(str(vm.exception),
                         'This query should return exactly one result. Your query returned 2')

    def test_combine_list(self):
        a = [1, 2, 3]
        b = ['a', 'b', 'c']
        c = combine_list(a, b)
        self.assertEqual([1, 2, 3, 'a', 'b', 'c'], c)

    def test_combine_dicts(self):
        a = {'username': 'boywonder', 'doc_type': 'goo'}
        b = {'email': 'boywonder@superteam.com', 'doc_type': 'foo'}
        c = combine_dicts(a, b)
        self.assertEqual({'username': 'boywonder',
                          'email': 'boywonder@superteam.com',
                          'doc_type': ['goo', 'foo']}, c)

    def test_local_backup(self):

        self.doc_class().backup('test-backup.json')
        dc = self.doc_class()
        self.assertEqual(3,
            len(dc.get_restore_json(*dc.get_path_type('test-backup.json'))))
        os.remove('test-backup.json')

    def test_local_restore(self):

        self.doc_class().backup('test-backup.json')
        self.doc_class().flush_db()
        self.assertEqual(len(list(self.doc_class.all())),0)
        self.doc_class().restore('test-backup.json')
        self.assertEqual(len(list(self.doc_class.all())), 3)
        os.remove('test-backup.json')

    def test_s3_backup(self):
        self.doc_class().backup(
            's3://{}/kev/test-backup.json'.format(env('S3_BUCKET_TEST')))
        dc = self.doc_class()
        self.assertEqual(3,
            len(dc.get_restore_json(
                *dc.get_path_type('s3://{}/kev/test-backup.json'.format(
                    env('S3_BUCKET_TEST'))))))

    def test_s3_restore(self):

        self.doc_class().backup(
            's3://{}/kev/test-backup.json'.format(env('S3_BUCKET_TEST')))
        for doc in self.doc_class.all():
            doc.delete()
        self.assertEqual(len(list(self.doc_class.all())),0)
        self.doc_class().restore('s3://{}/kev/test-backup.json'.format(env('S3_BUCKET_TEST')))
        self.assertEqual(len(list(self.doc_class.all())), 3)

    def test_limit_and_skip(self):
        self.assertEqual(3, len(list(self.doc_class.all(limit=4))))
        for x in range(1, 4):
            self.assertEqual(x, len(list(self.doc_class.all(limit=x))))
        self.assertEqual(2, len(list(self.doc_class.all(skip=1, limit=3))))
        self.assertEqual(0, len(list(self.doc_class.all(skip=3, limit=3))))
        with self.assertRaises(AttributeError):
            list(self.doc_class.all(limit=0))
        with self.assertRaises(AttributeError):
            list(self.doc_class.all(skip=-1))

    def test_sorting(self):
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('name')
        self.assertEqual(2, qs.count())
        self.assertEqual(qs[0].name, 'Goo and Sons')
        self.assertEqual(qs[1].name, 'Lakewoood YMCA')
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('name', reverse=True)
        self.assertEqual(qs[0].name, 'Lakewoood YMCA')
        self.assertEqual(qs[1].name, 'Goo and Sons')
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('gpa')
        self.assertEqual(qs[0].gpa, 3.0)
        self.assertEqual(qs[1].gpa, 3.2)
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('gpa', reverse=True)
        self.assertEqual(qs[0].gpa, 3.2)
        self.assertEqual(qs[1].gpa, 3.0)
        with self.assertRaises(ValueError) as vm:
            qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('nonexistent_field')
            qs.count()
            self.assertEqual(str(vm.exception),
                             "Field 'nonexistent_field' doesn't exists in a document")
        qs = self.doc_class.objects().all().sort_by('name')
        self.assertEqual(3, qs.count())
        self.assertEqual(qs[0].name, 'Goo and Sons')
        qs = self.doc_class.objects().all().sort_by('name', reverse=True)
        self.assertEqual(qs[2].name, 'Goo and Sons')

class RedisQueryTestCase(S3RedisQueryTestCase):

    doc_class = RedisTestDocumentSlug

    def test_sorting(self):
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('name')
        self.assertEqual(2, qs.count())
        self.assertEqual(qs[0].name, 'Goo and Sons')
        self.assertEqual(qs[1].name, 'Lakewoood YMCA')
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('name', reverse=True)
        self.assertEqual(qs[0].name, 'Lakewoood YMCA')
        self.assertEqual(qs[1].name, 'Goo and Sons')
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('gpa')
        self.assertEqual(qs[0].gpa, 3.0)
        self.assertEqual(qs[1].gpa, 3.2)
        qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('gpa', reverse=True)
        self.assertEqual(qs[0].gpa, 3.2)
        self.assertEqual(qs[1].gpa, 3.0)
        with self.assertRaises(ValueError) as vm:
            qs = self.doc_class.objects().filter({'city': 'Durham'}).sort_by('nonexistent_field')
            qs.count()
            self.assertEqual(str(vm.exception),
                             "Field 'nonexistent_field' doesn't exists in a document")
        qs = self.doc_class.objects().all().sort_by('name')
        self.assertEqual(3, qs.count())
        self.assertEqual(qs[0].name, 'Goo and Sons')
        qs = self.doc_class.objects().all().sort_by('name', reverse=True)
        self.assertEqual(qs[2].name, 'Goo and Sons')


class S3QueryTestCase(S3RedisQueryTestCase):

    doc_class = S3TestDocumentSlug

    def test_wildcard_queryset_chaining(self):
        qs = self.doc_class.objects().filter(
            {'name': 'Goo and Sons'}).filter({'city': 'Du*ham'})
        with self.assertRaises(ValueError):
            qs.count()


    def test_queryset_chaining(self):
        qs = self.doc_class.objects().filter(
            {'name': 'Goo and Sons'}).filter({'city': 'Durham'})
        with self.assertRaises(ValueError):
            qs.count()

    def test_non_unique_wildcard_filter(self):
        qs = self.doc_class.objects().filter({'city': 'du*ham'})
        self.assertEqual(2, qs.count())

    def test_non_unique_wildcard_filter(self):
        pass

    @unittest.skip("Takes more than 10 min to complete.")
    def test_more_than_hundred_objects(self):
        count = 1100
        for i in range(count):
            doc = self.doc_class(name='Object_{0}'.format(i), slug='object-{0}'.format(i), gpa=4.6,
                                 email='object_{0}@ymca.com'.format(i), city='Durham')
            doc.save()
        qs = self.doc_class.all()
        self.assertEqual(count + 3, len(list(qs)))
        for doc in list(qs):
            self.assertIn(doc.city, ['Durham', 'Charlotte'])


if __name__ == '__main__':
    unittest.main()
