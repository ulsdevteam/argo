from datetime import datetime
import elasticsearch_dsl as es
import shortuuid

from .analyzers import base_analyzer


class DateField(es.Date):
    """Custom Date field to support indexing dates without timezones."""
    def deserialize(self, data):
        data = super(DateField, self).deserialize(data)
        if isinstance(data, datetime):
            data = data.date()
        return data


class Date(es.InnerDoc):
    """Refers to a single date or date range.
    Used on Documents to create human and machine readable date representations.
    The `expression` field is intended to be a human readable representation of a date or date range,
    while the begin and end values are machine readable and actionable values.
    """
    begin = DateField(required=True)
    end = DateField()
    expression = es.Text(required=True)
    label = es.Text(required=True)
    type = es.Text(required=True)


class ExternalIdentifier(es.InnerDoc):
    """Abstract representation of external identifier object.
    Used on Documents to unambiguously tie them to source data.
    """
    identifier = es.Text(required=True)
    source = es.Text(required=True)
    source_identifier = es.Text()


class Extent(es.InnerDoc):
    """Refers to the size of a group of records."""
    type = es.Text(required=True)
    value = es.Float(required=True)


class Language(es.InnerDoc):
    """Refers to a human language."""
    expression = es.Text(required=True)
    identifier = es.Text(required=True)


class Subnote(es.InnerDoc):
    """Abstract wrapper for note content, associated with Note Documents."""
    content = es.Text(required=True, analyzer=base_analyzer)
    type = es.Text(required=True)


class Note(es.InnerDoc):
    """Abstract representation of notes, which are typed and contain human readable
    content in a Subnotes InnerDoc.
    """
    source = es.Text(required=True)
    subnotes = es.Object(Subnote, required=True)
    title = es.Text(required=True, analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(required=True)


class RightsGranted(es.InnerDoc):
    """Abstract wrapper for RightsGranted information, associated with a RightsStatement Document."""
    act = es.Text(required=True)
    begin = DateField(required=True)
    end = DateField(required=True)
    notes = es.Nested(Note)
    restriction = es.Text(required=True)


class RightsStatement(es.InnerDoc):
    """Machine readable representation of restrictions or permissions,
    generally related to a group of archival records. This structure is based
    on the PREservation Metadata: Implementation Strategies (PREMIS) Rights entity.
    """
    begin = DateField(required=True)
    copyright_status = es.Text()
    determination_date = DateField(required=True)
    end = DateField(required=True)
    jurisdiction = es.Text()
    notes = es.Nested(Note)
    other_basis = es.Text()
    rights_granted = es.Nested(RightsGranted, required=True)
    rights_type = es.Text(required=True)
    type = es.Text(required=True)


class BaseDescriptionComponent(es.Document):
    """Base class for DescriptionComponents and Reference objects with
    common fields."""

    component_reference = es.Join(relations={'component': 'reference'})
    external_identifiers = es.Nested(ExternalIdentifier, required=True)
    id = es.Text(required=True)
    title = es.Text(required=True, analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(required=True, fields={'keyword': es.Keyword()})

    @classmethod
    def _matches(cls, hit):
        """Ensures that this class is never used for deserialization."""
        return False

    def save(self, **kwargs):
        for e in self.external_identifiers:
            e.source_identifier = "{}_{}".format(e.source, e.identifier)
        return super(BaseDescriptionComponent, self).save(**kwargs)

    class Index:
        name = 'default'


class DescriptionComponent(BaseDescriptionComponent):
    """Wrapper for actual description elements"""
    @classmethod
    def _matches(cls, hit):
        """Ensure we only get components back."""
        return hit['_source']['component_reference'] == 'component'

    @classmethod
    def search(cls, **kwargs):
        return cls._index.search(**kwargs).filter('term', component_reference='component')

    def generate_id(self):
        return shortuuid.uuid()

    def add_reference(self, obj, relation):
        index = self.meta.index if ('index' in self.meta) else self._index._name
        identifier = self.generate_id()
        reference = Reference(
            _routing=self.meta.id,
            _index=index,
            _id=identifier,
            component_reference={'name': 'reference', 'parent': self.meta.id},
            id=identifier,
            relation=relation,
            uri='/collections/{}'.format(obj.meta.id),
            type=obj.type,
            title=obj.title,
            external_identifiers=obj.external_identifiers
        )
        reference.save()
        return reference

    def search_references(self, relation=None):
        s = Reference.search()
        s = s.filter('parent_id', type='reference', id=self.meta.id)
        if relation:
            s = s.filter('match_phrase', relation=relation)
        s = s.params(routing=self.meta.id)
        return s

    # TODO: this currently only returns 10 - need to return all
    def get_references(self, relation=None):
        """Get references from inner_hits already present or by searching."""
        if 'inner_hits' in self.meta and 'reference' in self.meta.inner_hits:
            return self.meta.inner_hits.reference.hits
        return list(self.search_references(relation))

    def save(self, **kwargs):
        self.component_reference = 'component'
        return super(DescriptionComponent, self).save(**kwargs)


class Reference(BaseDescriptionComponent):
    """A minimal reference to a Document."""
    uri = es.Text()
    order = es.Integer()
    relation = es.Text()

    @classmethod
    def _matches(cls, hit):
        """ Use Reference class for child documents with child name 'reference' """
        return isinstance(hit['_source']['component_reference'], dict) \
            and hit['_source']['component_reference'].get('name') == 'reference'

    @classmethod
    def search(cls, **kwargs):
        return cls._index.search(**kwargs).exclude('term', component_reference='component')

    def save(self, **kwargs):
        self.meta.routing = self.component_reference.parent
        return super(Reference, self).save(**kwargs)


class Agent(DescriptionComponent):
    """A person, organization or family that was involved in the creation and
    maintenance of records, or is the subject of those records.
    """
    description = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
    notes = es.Nested(Note)
    # collections = es.Nested(Reference)
    # objects = es.Nested(Reference)

    @classmethod
    def search(cls, **kwargs):
        search = super(Agent, cls).search(**kwargs)
        return search.filter('term', type='agent')

    def save(self, **kwargs):
        as_ids = [i for i in self.external_identifiers if i.source == 'archivesspace']
        for i in as_ids:
            parents = documents_by_external_id(Collection,
                                               "{}_{}".format(i.source, i.identifier),
                                               'agents__external_identifiers__source_identifier')
            for p in parents:
                # TODO: need to check to see if this exists first!
                self.add_reference(p, 'agent')
        return super(Agent, self).save(**kwargs)


class Collection(DescriptionComponent):
    """A group of archival records which contains other groups of records,
    and may itself be part of a larger Collection.  Collections are not
    physical groups of records, such as boxes and folders, but are intellectually
    significant aggregations which crucial to understanding the context of
    records creation and maintenance, such as record groups or series.
    """
    dates = es.Object(Date, required=True)
    extents = es.Nested(Extent, required=True)
    languages = es.Object(Language, required=True)
    level = es.Text(fields={'keyword': es.Keyword()})
    notes = es.Nested(Note)
    rights_statements = es.Nested(RightsStatement)

    @classmethod
    def search(cls, **kwargs):
        search = super(Collection, cls).search(**kwargs)
        return search.filter('term', type='collection')

    def save(self, **kwargs):
        as_ids = [i for i in self.external_identifiers if i.source == 'archivesspace']
        for i in as_ids:
            parents = documents_by_external_id(Collection,
                                               "{}_{}".format(i.source, i.identifier),
                                               'ancestors__external_identifiers__source_identifier')
            for p in parents:
                self.add_reference(p, 'ancestor')
        # this is probably the wrong way around. References should resolve themselves.
        # self.terms = resolve_references(self, 'archivesspace', Term, self.terms)
        # creators = resolve_references(self, 'archivesspace', Agent, self.creators)
        # self.agents = resolve_references(self, 'archivesspace', Agent, self.agents)
        # self.ancestors = resolve_references(self, 'archivesspace', Collection, self.ancestors)
        # self.children = resolve_references(self, 'archivesspace', Collection, self.children)
        return super(Collection, self).save(**kwargs)


class Object(DescriptionComponent):
    """A group of archival records which is part of a larger Collection,
    but does not contain any other aggregations.
    """
    dates = es.Object(Date, required=True)
    languages = es.Object(Language)
    extents = es.Nested(Extent, required=True)
    notes = es.Nested(Note)
    # agents = es.Nested(Reference)
    # terms = es.Nested(Reference)
    # ancestors = es.Nested(Reference)
    rights_statements = es.Nested(RightsStatement)

    @classmethod
    def search(cls, **kwargs):
        search = super(Object, cls).search(**kwargs)
        return search.filter('term', type='object')


class Term(DescriptionComponent):
    """A controlled term topical, geo"""
    # collections = es.Nested(Reference)
    # objects = es.Nested(Reference)

    @classmethod
    def search(cls, **kwargs):
        search = super(Term, cls).search(**kwargs)
        return search.filter('term', type='term')


def resolve_references(obj, source, doc_cls, ref_list):
    resolved = []
    for a in ref_list:
        identifiers = [i.identifier for i in a.external_identifiers if i.source == source]
        ident = identifiers[0] if len(identifiers) else None
        primary_doc = documents_by_external_id(doc_cls, ident, source)  # the document containing the information to resolve
        if primary_doc:
            for ext_id in primary_doc.external_identifiers:
                id_doc = documents_by_external_id(Reference, ext_id.identifier, ext_id.source, parent=obj)
                if not id_doc:
                    continue
                id_doc.title = primary_doc.title
                id_doc.type = primary_doc.type
                id_doc.external_identifiers = primary_doc.external_identifiers
                id_doc.uri = get_uri(primary_doc)
                id_doc.order = primary_doc.order if ('order' in primary_doc) else None
                id_doc.meta.parent = obj
                id_doc.save()
                resolved.append(id_doc)
    resolved = resolved if len(resolved) else None
    return resolved


def documents_by_external_id(doc_cls, ident, path):
    """Returns a list of documents which match an identifier at a particular path.

    NOTE: This should target the `source_identifier` field, which is a concatenation
    of the source and identifier. This covers the edge case of identifiers which
    are not unique between sources.
    """
    s = doc_cls.search()
    s = s.query('match_phrase', **{path: ident})
    return s


def get_uri(obj):
    return "{}/{}".format(obj.meta.index, obj.meta.id)
