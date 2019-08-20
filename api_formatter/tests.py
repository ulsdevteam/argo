import json
import os
import shortuuid

from django.test import TestCase
from django.urls import reverse
from elasticsearch_dsl import connections, Search, Index
from rest_framework.test import APIRequestFactory

from .elasticsearch.documents import Agent, Object, Term
from .views import AgentViewSet, ObjectViewSet, TermViewSet
from argo import settings

TYPE_MAP = (
    ('agents', Agent, AgentViewSet, 'agent-list', 'agent-detail'),
    ('objects', Object, ObjectViewSet, 'object-list', 'object-detail'),
    ('terms', Term, TermViewSet, 'term-list', 'term-detail'),
)

# TODO: test filtering, ordering, etc


class TestAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        connections.create_connection(hosts=settings.ELASTICSEARCH_DSL['default']['hosts'], timeout=60)
        for cls in [Agent, Object, Term]:
            cls.init()

    def index_fixture_data(self, source_filepath, doc_cls):
        added_ids = []
        source_filepath = os.path.join(settings.BASE_DIR, source_filepath)
        for f in os.listdir(source_filepath):
            with open(os.path.join(source_filepath, f)) as jf:
                data = json.load(jf)
                agent = doc_cls(**data)
                agent.meta.id = data['id']
                agent.save()
                added_ids.append(data['id'])
        return added_ids

    def list_view(self, view, viewset, obj_length):
        request = self.factory.get(reverse(view))
        response = viewset.as_view(actions={"get": "list"})(request)
        self.assertEqual(obj_length, int(response.data['count']),
                         "Number of documents in index for View {} did not match number indexed".format(view))

    def detail_view(self, view, viewset, pk):
        request = self.factory.get(reverse(view, args=[pk]))
        response = viewset.as_view(actions={"get": "retrieve"})(request, pk=pk)
        self.assertEqual(response.status_code, 200,
                         "View {} in ViewSet {} did not return 200 for document {}".format(view, viewset, pk))

    def test_documents(self):
        for t in TYPE_MAP:
            added_ids = self.index_fixture_data('fixtures/{}'.format(t[0]), t[1])
            Index(name=t[0]).refresh()
            self.list_view(t[3], t[2], len(added_ids))
            for ident in added_ids:
                self.detail_view(t[4], t[2], ident)
