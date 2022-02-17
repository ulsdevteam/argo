from datetime import datetime

from django.urls import reverse
from rest_framework import serializers

from .view_helpers import description_from_notes


class ExternalIdentifierSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    source = serializers.CharField()


class DateSerializer(serializers.Serializer):
    expression = serializers.CharField()
    begin = serializers.DateField()
    end = serializers.CharField(allow_null=True)
    label = serializers.DateField()
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

    def get_content(self, obj):
        """Coerce content into a list so it can be serialized as JSON."""
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
    copyright_status = serializers.CharField(allow_null=True)
    other_basis = serializers.CharField(allow_null=True)
    jurisdiction = serializers.CharField(allow_null=True)
    notes = NoteSerializer(many=True, allow_null=True)
    rights_granted = RightsGrantedSerializer(many=True)


class GroupSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    title = serializers.CharField()


class ReferenceSerializer(serializers.Serializer):
    title = serializers.CharField()
    type = serializers.CharField(allow_null=True)
    online = serializers.SerializerMethodField()
    hit_count = serializers.IntegerField(allow_null=True)
    online_hit_count = serializers.IntegerField(allow_null=True)
    uri = serializers.SerializerMethodField()
    dates = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    group = GroupSerializer(allow_null=True)
    index = serializers.IntegerField(source="position", allow_null=True)

    def get_online(self, obj):
        return getattr(obj, "online", False)

    def get_uri(self, obj):
        if getattr(obj, "uri", None):
            return obj.uri.rstrip('/')
        basename = obj.type
        if basename in ["person", "organization", "family", "software"]:
            basename = "agent"
        return reverse('{}-detail'.format(basename), kwargs={"pk": obj.identifier})


class BaseListSerializer(serializers.Serializer):
    uri = serializers.SerializerMethodField()
    type = serializers.CharField()
    title = serializers.CharField()
    dates = DateSerializer(many=True, allow_null=True)

    def get_uri(self, obj):
        basename = self.context.get('view').basename or obj.type
        return reverse('{}-detail'.format(basename), kwargs={"pk": obj.meta.id})


class BaseDetailSerializer(serializers.Serializer):
    uri = serializers.SerializerMethodField()
    title = serializers.CharField()
    type = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    offset = serializers.IntegerField(allow_null=True)
    group = GroupSerializer()
    external_identifiers = ExternalIdentifierSerializer(many=True)

    def get_uri(self, obj):
        basename = self.context.get('view').basename or obj.type
        return reverse('{}-detail'.format(basename), kwargs={"pk": obj.meta.id})


class AgentSerializer(BaseDetailSerializer):
    agent_type = serializers.CharField()
    authorized_name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    dates = DateSerializer(many=True, allow_null=True)
    notes = NoteSerializer(many=True, allow_null=True)


class AgentListSerializer(BaseListSerializer):
    pass


class CollectionSerializer(BaseDetailSerializer):
    level = serializers.CharField()
    parent = serializers.CharField(allow_null=True)
    languages = LanguageSerializer(many=True, allow_null=True)
    description = serializers.SerializerMethodField()
    extents = ExtentSerializer(many=True)
    formats = serializers.ListField()
    online = serializers.BooleanField()
    dates = DateSerializer(many=True, allow_null=True)
    notes = NoteSerializer(many=True, allow_null=True)
    rights_statements = RightsStatementSerializer(many=True, allow_null=True)
    agents = ReferenceSerializer(many=True, allow_null=True)
    creators = ReferenceSerializer(many=True, allow_null=True)
    terms = ReferenceSerializer(many=True, allow_null=True)

    def get_description(self, obj):
        return description_from_notes(getattr(obj, "notes", []))


class CollectionListSerializer(BaseListSerializer):
    pass


class ObjectSerializer(BaseDetailSerializer):
    languages = LanguageSerializer(many=True, allow_null=True)
    parent = serializers.CharField(allow_null=True)
    description = serializers.SerializerMethodField()
    extents = ExtentSerializer(many=True, allow_null=True)
    formats = serializers.ListField()
    online = serializers.BooleanField()
    dates = DateSerializer(many=True, allow_null=True)
    notes = NoteSerializer(many=True, allow_null=True)
    rights_statements = RightsStatementSerializer(many=True, allow_null=True)
    agents = ReferenceSerializer(many=True, allow_null=True)
    terms = ReferenceSerializer(many=True, allow_null=True)

    def get_description(self, obj):
        return description_from_notes(getattr(obj, "notes", []))


class ObjectListSerializer(BaseListSerializer):
    pass


class TermSerializer(BaseDetailSerializer):
    term_type = serializers.CharField()
    collections = ReferenceSerializer(many=True, allow_null=True)
    objects = ReferenceSerializer(many=True, allow_null=True)


class TermListSerializer(BaseListSerializer):
    pass


class CollectionHitSerializer(serializers.Serializer):
    """Serializes data for collapsed hits."""
    category = serializers.CharField(source="group.category")
    dates = serializers.SerializerMethodField()
    hit_count = serializers.IntegerField()
    online_hit_count = serializers.IntegerField(allow_null=True)
    title = serializers.CharField(source="group.title")
    uri = serializers.SerializerMethodField()
    creators = serializers.SerializerMethodField()

    def get_dates(self, obj):
        return [d.to_dict() for d in obj.group.dates]

    def get_creators(self, obj):
        if getattr(obj.group, "creators", None):
            return [c.title for c in obj.group.creators]
        else:
            return []

    def get_uri(self, obj):
        return obj.group.identifier.rstrip("/")


class FacetSerializer(serializers.Serializer):
    """Serializes facets."""

    def to_representation(self, instance):
        resp = {}
        for k, v in instance.aggregations.to_dict().items():
            if "buckets" in v:
                resp[k] = v["buckets"]
            elif "name" in v:  # move nested aggregations up one level
                resp[k] = v["name"]["buckets"]
            elif k in ["max_date", "min_date"]:  # convert timestamps to year
                value = (datetime.fromtimestamp(v["value"] / 1000.0).year) if v["value"] else None
                resp[k] = {"value": value}
            else:
                resp[k] = v
        return resp


class AncestorsSerializer(serializers.Serializer):
    """Provides a nested dictionary representation of ancestors."""

    def serialize_ancestors(self, ancestor_list, tree, idx):
        ancestor = ancestor_list[idx]
        serialized = ReferenceSerializer(ancestor).data
        tree_data = {**serialized, **tree}
        if idx == len(ancestor_list) - 1:
            new_tree = tree_data
            return new_tree
        else:
            new_tree = {"child": tree_data}
            return self.serialize_ancestors(ancestor_list, new_tree, idx + 1)

    def to_representation(self, instance):
        resp = {}
        if instance:
            resp = self.serialize_ancestors(instance, {}, 0)
        return resp
