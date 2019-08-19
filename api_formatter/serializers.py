from rest_framework import serializers
from rest_framework.fields import empty
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer

from .elasticsearch.documents import Agent


class DateSerializer(serializers.Serializer):
    expression = serializers.CharField()
    begin = serializers.DateField()
    end = serializers.DateField()
    label = serializers.CharField()
    type = serializers.CharField()


class SubnoteSerializer(serializers.Serializer):
    type = serializers.CharField()
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        # content needs to be coerced to a list so it can be serialized as JSON
        return list(obj.content)


class NoteSerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    source = serializers.CharField()
    subnotes = SubnoteSerializer(many=True)


class ExternalIdentifierSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    source = serializers.CharField()


class AgentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    dates = DateSerializer(many=True)
    notes = NoteSerializer(many=True)
    external_identifiers = ExternalIdentifierSerializer(many=True)


class AgentListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
