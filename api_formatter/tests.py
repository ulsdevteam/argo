import datetime
import json
import os
import random

from argo import settings
from django.test import TestCase
from django.urls import reverse
from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import connections, utils
from rac_es.documents import (Agent, BaseDescriptionComponent, Collection,
                              Object, Term)
from rac_schemas import is_valid
from rest_framework.test import APIRequestFactory

from .views import AgentViewSet, CollectionViewSet, ObjectViewSet, TermViewSet

TYPE_MAP = (
    ('agent', Agent, AgentViewSet),
    ('collection', Collection, CollectionViewSet),
    ('object', Object, ObjectViewSet),
    ('term', Term, TermViewSet),
)

STOP_WORDS = ["a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if",
              "in", "into", "is", "it", "no", "not", "of", "on", "or", "such",
              "that", "the", "their", "then", "there", "these", "they", "this",
              "to", "was", "will", "with", "-", "--"]


class TestAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.connection = connections.create_connection(hosts=settings.ELASTICSEARCH_DSL['default']['hosts'], timeout=60)
        BaseDescriptionComponent.init()

    def validate_fixtures(self):
        print("Validating fixtures")
        for dir in os.listdir(os.path.join(settings.BASE_DIR, 'fixtures')):
            if os.path.isdir(os.path.join(settings.BASE_DIR, 'fixtures', dir)):
                for f in os.listdir(os.path.join(settings.BASE_DIR, 'fixtures', dir)):
                    with open(os.path.join(settings.BASE_DIR, 'fixtures', dir, f), 'r') as jf:
                        instance = json.load(jf)
                        self.assertTrue(is_valid(instance, "{}.json".format(instance["type"])))

    def prepare_data(self, source_filepath, doc_cls):
        source_filepath = os.path.join(settings.BASE_DIR, source_filepath)
        for f in os.listdir(source_filepath):
            with open(os.path.join(source_filepath, f)) as jf:
                data = json.load(jf)
                doc = doc_cls(**data)
                yield doc.prepare_streaming_dict(data["uri"].split("/")[-1])

    def index_fixture_data(self, source_filepath, doc_cls):
        added_ids = []
        for ok, result in streaming_bulk(self.connection, self.prepare_data(source_filepath, doc_cls), refresh=True):
            action, result = result.popitem()
            if not ok:
                raise Exception("Failed to {} document {}: {}".format(action, result["_id"], result))
            else:
                added_ids.append(result["_id"])
        return added_ids

    def get_nested_value(self, key_list, obj):
        child_obj = getattr(obj, key_list[0])
        key_list.pop(0)
        if len(key_list) > 0:
            if isinstance(child_obj, utils.AttrList):
                return self.get_nested_value(key_list, child_obj[0])
            else:
                return self.get_nested_value(key_list, child_obj)
        if (isinstance(child_obj, datetime.datetime) or isinstance(child_obj, datetime.date)):
            return child_obj.strftime('%Y')
        if isinstance(child_obj, utils.AttrList):
            child_obj = child_obj[0]
        return (child_obj if child_obj else "")

    def get_random_word(self, word_list):
        """Returns a random lowercased word from a list."""
        w = word_list[random.randint(0, len(word_list) - 1)].lower()
        if w in STOP_WORDS:
            word_list.remove(w)
            print("{} found in stop words, trying again from list {}".format(w, word_list))
            return self.get_random_word(word_list)
        return w

    def get_random_obj(self, obj_list, cls):
        uuid = random.choice(obj_list.data.get('results')).get('uri').split('/')[2]
        return cls.get(id=uuid)

    def find_in_dict(self, dictionary, key):
        for k, v in dictionary.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in self.find_in_dict(v, key):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    if isinstance(d, dict):
                        for result in self.find_in_dict(d, key):
                            yield result

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
        self.assertEqual(
            obj_length, int(response.data['count']),
            "Number of documents in index for View {} did not match number indexed".format(
                "{}-list".format(basename)))
        self.sort_fields(viewset, basename, base_url)
        obj = self.get_random_obj(response, model_cls)
        self.filter_fields(viewset, base_url, basename, obj)
        self.search_fields(viewset, base_url, basename, obj)

    def detail_view(self, basename, viewset, pk):
        request = self.factory.get(reverse("{}-detail".format(basename), args=[pk]))
        response = viewset.as_view(actions={"get": "retrieve"}, basename=basename)(request, pk=pk)
        self.assertEqual(
            response.status_code, 200,
            "View {}-detail in ViewSet {} did not return 200 for document {}".format(
                basename, viewset, pk))
        for uri in self.find_in_dict(response.data, "uri"):
            self.assertFalse(uri.endswith("/"))
        if basename in ["collection", "object"]:
            self.assertTrue(isinstance(response.data["online"], bool))

    def ancestors_view(self, basename, viewset, pk):
        request = self.factory.get(reverse("{}-ancestors".format(basename), args=[pk]))
        response = viewset.as_view(actions={"get": "retrieve"}, basename=basename)(request, pk=pk)
        self.assertEqual(
            response.status_code, 200,
            "View {}-ancestors in ViewSet {} did not return 200 for document {}".format(
                basename, viewset, pk))

    def children_view(self, viewset, pk):
        request = self.factory.get(reverse("collection-children", args=[pk]))
        response = viewset.as_view(actions={"get": "retrieve"}, basename="collection")(request, pk=pk)
        self.assertEqual(
            response.status_code, 200,
            "View collection-children in ViewSet {} did not return 200 for document {}".format(
                viewset, pk))
        for child in response.data.results:
            self.assertTrue(isinstance(child["online"], bool))

    def test_documents(self):
        self.validate_fixtures()
        for doc_type, doc_cls, viewset in TYPE_MAP:
            added_ids = self.index_fixture_data('fixtures/{}'.format(doc_type), doc_cls)
            self.list_view(doc_cls, doc_type, viewset, len(added_ids))
            for ident in added_ids:
                self.detail_view(doc_type, viewset, ident)
                if doc_type in ["collection", "object"]:
                    self.ancestors_view(doc_type, viewset, ident)
                if doc_type == "collection":
                    self.children_view(viewset, ident)

    def test_schema(self):
        schema = self.client.get(reverse('schema'))
        self.assertEqual(schema.status_code, 200, "Wrong HTTP code")
