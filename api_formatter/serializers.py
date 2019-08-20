from rest_framework import serializers

# TODO: check on date versus datetime
# TODO: consistent naming for date start and end
# TODO: camel case versus snake case
# TODO: allow_null fields


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


class ExternalIdentifierSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    source = serializers.CharField()


class ExtentSerializer(serializers.Serializer):
    value = serializers.FloatField()
    type = serializers.CharField()


class LanguageSerializer(serializers.Serializer):
    expression = serializers.CharField()
    identifier = serializers.CharField()


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


class RightsGrantedSerializer(serializers.Serializer):
    act = serializers.CharField()
    dateStart = serializers.DateField()
    dateEnd = serializers.DateField()
    restriction = serializers.CharField()
    notes = NoteSerializer(many=True)


class RightsStatementSerializer(serializers.Serializer):
    determinationDate = serializers.DateField()
    type = serializers.CharField()
    rightsType = serializers.CharField()
    dateStart = serializers.DateField()
    dateEnd = serializers.DateField()
    copyrightStatus = serializers.CharField()
    otherBasis = serializers.CharField()
    jurisdiction = serializers.CharField()
    notes = NoteSerializer(many=True)
    rights_granted = RightsGrantedSerializer(many=True)


class URISerializer(serializers.Serializer):
    ref = serializers.CharField()


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


class ObjectSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    type = serializers.CharField()
    dates = DateSerializer(many=True)
    languages = LanguageSerializer(many=True)
    extents = ExtentSerializer(many=True)
    notes = NoteSerializer(many=True, allow_null=True)
    rights_statements = RightsStatementSerializer(many=True, allow_null=True)
    external_identifiers = ExternalIdentifierSerializer(many=True)
    agents = URISerializer(many=True, allow_null=True)
    terms = URISerializer(many=True, allow_null=True)
    ancestors = AncestorSerializer(allow_null=True)
    children = ChildrenSerializer(allow_null=True)


class ObjectListSerializer(serializers.Serializer):
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
