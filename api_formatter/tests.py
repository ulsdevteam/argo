import json
import os
import shortuuid

from django.test import TestCase
from django.urls import reverse
from elasticsearch_dsl import connections, Search
from rest_framework.test import APIRequestFactory

from .elasticsearch.documents import Agent, Term
from .views import AgentViewSet, TermViewSet
from argo import settings


class TestAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        connections.create_connection(hosts=settings.ELASTICSEARCH_DSL['default']['hosts'], timeout=60)
        for cls in [Agent, Term]:
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
        self.assertEqual(obj_length, int(response.data['count']))

    def detail_view(self, view, viewset, pk):
        request = self.factory.get(reverse(view, args=[pk]))
        response = viewset.as_view(actions={"get": "retrieve"})(request, pk=pk)
        self.assertEqual(response.status_code, 200)

    def test_agents(self):
        added_ids = self.index_fixture_data('fixtures/agents', Agent)
        self.list_view('agent-list', AgentViewSet, len(added_ids))
        for agent_id in added_ids:
            self.detail_view('agent-detail', AgentViewSet, agent_id)

    def test_terms(self):
        added_ids = self.index_fixture_data('fixtures/terms', Term)
        self.list_view('term-list', TermViewSet, len(added_ids))
        for term_id in added_ids:
            self.detail_view('term-detail', TermViewSet, term_id)
