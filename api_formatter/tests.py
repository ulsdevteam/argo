import json
import os
import shortuuid

from django.test import TestCase
from django.urls import reverse
from elasticsearch_dsl import connections, Search
from rest_framework.test import APIRequestFactory

from .elasticsearch.documents import Agent
from .views import AgentViewSet
from argo import settings


class TestAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        connections.create_connection(hosts=settings.ELASTICSEARCH_DSL['default']['hosts'], timeout=60)
        for cls in [Agent]:
            cls.init()

    def index_fixture_data(self, source_filepath, index, doc_cls):
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

    def test_agents(self):
        agent_ids = self.index_fixture_data('fixtures/agents', 'agents', Agent)

        # test length of list response
        request = self.factory.get(reverse('agent-list'))
        agent_list = AgentViewSet.as_view(actions={"get": "list"})(request)
        self.assertEqual(len(agent_ids), int(agent_list.data['count']))

        # test individual responses
        for agent in agent_ids:
            request = self.factory.get(reverse('agent-detail', args=[agent]))
            response = AgentViewSet.as_view(actions={"get": "retrieve"})(request, pk=agent)
            self.assertEqual(response.status_code, 200)
