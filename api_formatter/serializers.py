from django.urls import reverse
from rest_framework import serializers

# TODO: check on date versus datetime
# TODO: allow_null fields


class ExternalIdentifierSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    source = serializers.CharField()


class AncestorSerializer(serializers.Serializer):
    # TODO: add ancestor serializer
    pass


class ChildrenSerializer(serializers.Serializer):
    # TODO: add children serializer
    pass


class DateSerializer(serializers.Serializer):
    expression = serializers.CharField()
    begin = serializers.DateField()
    end = serializers.DateField()
    label = serializers.CharField()
    type = serializers.CharField()


class ExtentSerializer(serializers.Serializer):
    value = serializers.FloatField()
    type = serializers.CharField()


class LanguageSerializer(serializers.Serializer):
    expression = serializers.CharField()
    identifier = serializers.CharField()


class SubnoteSerializer(serializers.Serializer):
    type = serializers.CharField()
    content = serializers.SerializerMethodField()

    # content needs to be coerced to a list so it can be serialized as JSON
    def get_content(self, obj):
        return list(obj.content)


class NoteSerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    source = serializers.CharField()
    subnotes = SubnoteSerializer(many=True)


class RightsGrantedSerializer(serializers.Serializer):
    act = serializers.CharField()
    begin = serializers.DateField()
    end = serializers.DateField()
    restriction = serializers.CharField()
    notes = NoteSerializer(many=True, allow_null=True)


class RightsStatementSerializer(serializers.Serializer):
    determination_date = serializers.DateField()
    type = serializers.CharField()
    rights_type = serializers.CharField()
    begin = serializers.DateField()
    end = serializers.DateField()
    copyright_status = serializers.CharField()
    other_basis = serializers.CharField()
    jurisdiction = serializers.CharField()
    notes = NoteSerializer(many=True, allow_null=True)
    rights_granted = RightsGrantedSerializer(many=True)


# TODO: this needs to be updated
class URISerializer(serializers.Serializer):
    ref = serializers.CharField()


class BaseListSerializer(serializers.Serializer):
    uri = serializers.SerializerMethodField()
    title = serializers.CharField()

    def get_uri(self, obj):
        try:
            return reverse('{}-detail'.format(self.context.get('view').basename), kwargs={"pk": obj.id})
        except:
            return "{}/{}".format(obj.meta.index, obj.id)


class BaseDetailSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    type = serializers.CharField()
    external_identifiers = ExternalIdentifierSerializer(many=True)


class AgentSerializer(BaseDetailSerializer):
    description = serializers.CharField()
    notes = NoteSerializer(many=True)


class AgentListSerializer(BaseListSerializer): pass


class CollectionSerializer(BaseDetailSerializer):
    level = serializers.CharField()
    languages = LanguageSerializer(many=True)
    extents = ExtentSerializer(many=True)
    dates = DateSerializer(many=True)
    notes = NoteSerializer(many=True, allow_null=True)
    rights_statements = RightsStatementSerializer(many=True, allow_null=True)
    agents = URISerializer(many=True, allow_null=True)
    creators = URISerializer(many=True, allow_null=True)
    terms = URISerializer(many=True, allow_null=True)
    ancestors = AncestorSerializer(allow_null=True)
    children = ChildrenSerializer(allow_null=True)


class CollectionListSerializer(BaseListSerializer): pass


class ObjectSerializer(BaseDetailSerializer):
    languages = LanguageSerializer(many=True)
    extents = ExtentSerializer(many=True)
    dates = DateSerializer(many=True)
    notes = NoteSerializer(many=True, allow_null=True)
    rights_statements = RightsStatementSerializer(many=True, allow_null=True)
    agents = URISerializer(many=True, allow_null=True)
    terms = URISerializer(many=True, allow_null=True)
    ancestors = AncestorSerializer(allow_null=True)


class ObjectListSerializer(BaseListSerializer): pass


class TermSerializer(BaseDetailSerializer): pass


class TermListSerializer(BaseListSerializer): pass


class HitSerializer(BaseListSerializer):
    type = serializers.CharField()
    dates = DateSerializer(many=True, allow_null=True)
    extents = ExtentSerializer(many=True, allow_null=True)
    agents = URISerializer(many=True, allow_null=True)
    terms = URISerializer(many=True, allow_null=True)
