from rest_framework import serializers


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
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    type = serializers.CharField()
    dates = DateSerializer(many=True)
    notes = NoteSerializer(many=True)
    external_identifiers = ExternalIdentifierSerializer(many=True)


class AgentListSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()


class TermSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    type = serializers.CharField()
    external_identifiers = ExternalIdentifierSerializer(many=True)


class TermListSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
