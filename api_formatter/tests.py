from datetime import datetime
import json
from jsonschema import validate
import os
import random
from functools import reduce
import shortuuid

from django.test import TestCase
from django.urls import reverse
from elasticsearch_dsl import connections, Search, Index, utils
from rest_framework.test import APIRequestFactory

from .elasticsearch.documents import Agent, BaseDescriptionComponent, Collection, Object, Term
from .views import AgentViewSet, CollectionViewSet, ObjectViewSet, TermViewSet
from argo import settings

TYPE_MAP = (
    ('agents', Agent, AgentViewSet, 'agent'),
    ('collections', Collection, CollectionViewSet, 'collection'),
    ('objects', Object, ObjectViewSet, 'object'),
    ('terms', Term, TermViewSet, 'term'),
)

STOP_WORDS = ["a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if",
              "in", "into", "is", "it", "no", "not", "of", "on", "or", "such",
              "that", "the", "their", "then", "there", "these", "they", "this",
              "to", "was", "will", "with"]


class TestAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        connections.create_connection(hosts=settings.ELASTICSEARCH_DSL['default']['hosts'], timeout=60)
        BaseDescriptionComponent.init()

    def validate_fixtures(self):
        print("Validating fixtures")
        with open(os.path.join(settings.BASE_DIR, 'rac-data-model', 'schema.json')) as sf:
            schema = json.load(sf)
            for dir in os.listdir(os.path.join(settings.BASE_DIR, 'fixtures')):
                if os.path.isdir(os.path.join(settings.BASE_DIR, 'fixtures', dir)):
                    for f in os.listdir(os.path.join(settings.BASE_DIR, 'fixtures', dir)):
                        with open(os.path.join(settings.BASE_DIR, 'fixtures', dir, f), 'r') as jf:
                            instance = json.load(jf)
                            valid = validate(instance=instance, schema=schema)
                            self.assertEqual(valid, None)

    def index_fixture_data(self, source_filepath, doc_cls):
        added_ids = []
        source_filepath = os.path.join(settings.BASE_DIR, source_filepath)
        for f in os.listdir(source_filepath):
            with open(os.path.join(source_filepath, f)) as jf:
                data = json.load(jf)
                object = doc_cls(**data)
                object.meta.id = data['id']
                object.save()
                added_ids.append(data['id'])
        return added_ids

    def get_nested_value(self, key_list, obj):
        child_obj = getattr(obj, key_list[0])
        key_list.pop(0)
        if len(key_list) > 0:
            if isinstance(child_obj, utils.AttrList):
                return self.get_nested_value(key_list, child_obj[0])
            else:
                return self.get_nested_value(key_list, child_obj)
        if isinstance(child_obj, datetime):
            return child_obj.strftime('%Y-%m-%d')
        return (child_obj if child_obj else "")

    def get_random_word(self, word_list):
        """Returns a random lowercased word from a list."""
        w = word_list[random.randint(0, len(word_list)-1)].lower()
        if w in STOP_WORDS:
            word_list.remove(w)
            print("{} found in stop words, trying again from list {}".format(w, word_list))
            self.get_random_word(word_list)
        return w

    def get_random_obj(self, obj_list, cls):
        uuid = random.choice(obj_list.data.get('results')).get('uri').split('/')[2]
        return cls.get(id=uuid)

    def sort_fields(self, viewset, basename, base_url):
        """
        Tests ascending and descending sort on ordering fields
        """
        for field in viewset.ordering_fields:
            for sort in [field, "-{}".format(field)]:
                url = "{}?sort={}".format(base_url, sort)
                print(url)
                sorted = self.factory.get(url)
                sort_response = viewset.as_view(actions={"get": "list"}, basename=basename)(sorted)
                self.assertEqual(sort_response.status_code, 200)
                self.assertTrue(sort_response.data.get('count') > 0)

    def filter_fields(self, viewset, base_url, basename, obj):
        """
        Use the field value from a random object as a filter value.
        This ensures we always have at least one result.
        """
        for field in viewset.filter_fields:
            field_list = viewset.filter_fields[field].get('field').rsplit('.keyword')[0].split('.')
            value = self.get_nested_value(field_list, obj)
            url = "{}?{}={}".format(base_url, field, value)
            print(url)
            filtered = self.factory.get(url)
            filter_response = viewset.as_view(actions={"get": "list"}, basename=basename)(filtered)
            self.assertEqual(filter_response.status_code, 200)
            self.assertTrue(filter_response.data.get('count') > 0)

    def search_fields(self, viewset, base_url, basename, obj):
        """
        Use the field value from a random object as a query value, unless it is None.
        This ensures we always have at least one result.
        """
        for field in viewset.search_fields:
            field_list = field.rsplit('.keyword')[0].split('.')
            value = self.get_nested_value(field_list, obj)
            query = self.get_random_word(value.split(" "))
            if query:
                url = "{}?query={}".format(base_url, query)
                print(url)
                search = self.factory.get(url)
                search_response = viewset.as_view(actions={"get": "list"}, basename=basename)(search)
                self.assertEqual(search_response.status_code, 200)
                self.assertTrue(search_response.data.get('count') > 0)

    def list_view(self, model_cls, basename, viewset, obj_length):
        base_url = reverse("{}-list".format(basename))
        base_viewset = viewset.as_view(actions={"get": "list"}, basename=basename)
        request = self.factory.get(base_url)
        response = base_viewset(request)
        # self.assertEqual(obj_length, int(response.data['count']),
        #                  "Number of documents in index for View {} did not match \
        #                   number indexed".format("{}-list".format(basename)))
        self.sort_fields(viewset, basename, base_url)
        obj = self.get_random_obj(response, model_cls)
        self.filter_fields(viewset, base_url, basename, obj)
        self.search_fields(viewset, base_url, basename, obj)

    def detail_view(self, basename, viewset, pk):
        request = self.factory.get(reverse("{}-detail".format(basename), args=[pk]))
        response = viewset.as_view(actions={"get": "retrieve"}, basename=basename)(request, pk=pk)
        self.assertEqual(response.status_code, 200,
                         "View {}-detail in ViewSet {} did not return 200 \
                         for document {}".format(basename, viewset, pk))

    def test_documents(self):
        self.validate_fixtures()
        for t in TYPE_MAP:
            added_ids = self.index_fixture_data('fixtures/{}'.format(t[0]), t[1])
            Index('default').refresh()
            self.list_view(t[1], t[3], t[2], len(added_ids))
            for ident in added_ids:
                self.detail_view(t[3], t[2], ident)

    def test_schema(self):
        schema = self.client.get(reverse('schema'))
        self.assertEqual(schema.status_code, 200, "Wrong HTTP code")
