# This avoids name collisions between Object class in elasticsearch_dsl and our Object Document class
import elasticsearch_dsl as es

from .analyzers import base_analyzer
# from .helpers import resolve_reference


class ExternalIdentifier(es.InnerDoc):
    """Abstract representation of external identifier object.
    Used on Documents to unambiguously tie them to source data.
    """
    source = es.Text(required=True)
    identifier = es.Text(required=True)


class Extent(es.InnerDoc):
    """Refers to the size of a group of records."""
    value = es.Float(required=True)
    type = es.Text(required=True)


class Date(es.InnerDoc):
    """Refers to a single date or date range.
    Used on Documents to create human and machine readable date representations.
    The `expression` field is intended to be a human readable representation of a date or date range,
    while the begin and end values are machine readable and actionable values.
    """
    begin = es.Date(required=True)
    end = es.Date()
    expression = es.Text(required=True)
    type = es.Text(required=True)
    label = es.Text(required=True)


class Language(es.InnerDoc):
    """Refers to a human language."""
    expression = es.Text(required=True)
    identifier = es.Text(required=True)


class Subnote(es.InnerDoc):
    """Abstract wrapper for note content, associated with Note Documents."""
    type = es.Text(required=True)
    content = es.Text(required=True, analyzer=base_analyzer)


class Note(es.InnerDoc):
    """Abstract representation of notes, which are typed and contain human readable
    content in a Subnotes InnerDoc.
    """
    type = es.Text(required=True)
    title = es.Text(required=True, analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    source = es.Text(required=True)
    subnotes = es.Object(Subnote, required=True)


class Reference(es.Document):
    """Abstract reference to a Document, which likely exists in a different index.
    On initial indexing, reference may only consist of an external_identifiers array,
    but additional data will likely be added during indexing.
    """
    title = es.Text(analyzer=base_analyzer)
    uri = es.Text()
    type = es.Text()
    order = es.Integer()
    external_identifiers = es.Nested(ExternalIdentifier, required=True)

    class Index:
        name = 'references'


class RightsGranted(es.InnerDoc):
    """Abstract wrapper for RightsGranted information, associated with a RightsStatement Document."""
    act = es.Text(required=True)
    begin = es.Date(required=True)
    end = es.Date(required=True)
    restriction = es.Text(required=True)
    notes = es.Nested(Note)


class RightsStatement(es.InnerDoc):
    """Machine readable representation of restrictions or permissions,
    generally related to a group of archival records. This structure is based
    on the PREservation Metadata: Implementation Strategies (PREMIS) Rights entity.
    """
    determination_date = es.Date(required=True)
    type = es.Text(required=True)
    rights_type = es.Text(required=True)
    begin = es.Date(required=True)
    end = es.Date(required=True)
    copyright_status = es.Text()
    other_basis = es.Text()
    jurisdiction = es.Text()
    notes = es.Nested(Note)
    rights_granted = es.Nested(RightsGranted, required=True)


class Agent(es.Document):
    """A person, organization or family that was involved in the creation and
    maintenance of records, or is the subject of those records.
    """
    id = es.Text(required=True)
    title = es.Text(required=True, analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    description = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(required=True, fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
    notes = es.Nested(Note)
    # collections = es.Nested(Reference)
    # objects = es.Nested(Reference)
    external_identifiers = es.Nested(ExternalIdentifier, required=True)

    class Index:
        name = 'agents'


class Collection(es.Document):
    """A group of archival records which contains other groups of records,
    and may itself be part of a larger Collection.  Collections are not
    physical groups of records, such as boxes and folders, but are intellectually
    significant aggregations which crucial to understanding the context of
    records creation and maintenance, such as record groups or series.
    """
    id = es.Text(required=True)
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(required=True, fields={'keyword': es.Keyword()})
    level = es.Text(fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
    languages = es.Object(Language)
    extents = es.Nested(Extent, required=True)
    notes = es.Nested(Note)
    # creators = es.Nested(Reference, required=True)  # TODO: should this be part of agents?
    # agents = es.Nested(Reference)
    # terms = es.Nested(Reference)
    # ancestors = es.Nested(Reference)
    # children = es.Nested(Reference)
    rights_statements = es.Nested(RightsStatement)
    external_identifiers = es.Nested(ExternalIdentifier, required=True)

    class Index:
        name = 'collections'

    def save(self, *args, **kwargs):
        ancestors = []
        for a in self.ancestors:
            resolved = resolve_reference(self, 'archivesspace', Collection)  # TODO: check first whether object or collection
            if resolved:
                ancestors.append(resolved)
        self.ancestors = list(set(ancestors)) if len(set(ancestors)) else None
        return super(Collection, self).save(*args, **kwargs)


class Object(es.Document):
    """A group of archival records which is part of a larger Collection,
    but does not contain any other aggregations.
    """
    id = es.Text(required=True)
    title = es.Text(required=True, analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(required=True, fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
    languages = es.Object(Language)
    extents = es.Nested(Extent)
    notes = es.Nested(Note)
    # agents = es.Nested(Reference)
    # terms = es.Nested(Reference)
    # ancestors = es.Nested(Reference)
    rights_statements = es.Nested(RightsStatement)
    external_identifiers = es.Nested(ExternalIdentifier, required=True)

    class Index:
        name = 'objects'


class Term(es.Document):
    """A controlled term topical, geo"""
    id = es.Text(required=True)
    title = es.Text(required=True, analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(required=True, fields={'keyword': es.Keyword()})
    # collections = es.Nested(Reference)
    # objects = es.Nested(Reference)
    external_identifiers = es.Nested(ExternalIdentifier, required=True)

    class Index:
        name = 'terms'


def resolve_reference(obj, source, doc_cls):
    ident = [i.identifier for i in obj.external_identifiers if i.source == source][0]
    print(ident)
    primary_doc = document_by_external_id(doc_cls, ident, source)
    if primary_doc:
        for ext_id in primary_doc.external_identifiers:
            id_doc = document_by_external_id(ExternalIdentifier, ext_id.identifier, ext_id.source, parent=obj)
            if not id_doc:
                e = ExternalIdentifier(title=primary_doc.title,
                                       type=primary_doc.type,
                                       external_identifiers=primary_doc.external_identifiers)
                e.uri = get_uri()
                e.order = primary_doc.order if primary_doc.order else None
                e.meta.parent = obj
                # do we explicitly set the parent here? There are likely to be multiple references to the same object...
                # another option is to look for existing children of this parent obj...
                # but if we're creating a new ref for each parent, do we need to nest external_identifiers???
                e.save()
            return e


def document_by_external_id(doc_cls, ident, source, parent=None):
    client = es.connections.get_connection(
        doc_cls._get_using()
    )
    search = es.Search(
        using=client,
        index=doc_cls._index._name,
        doc_type=doc_cls._doc_type.name
    )
    q = search.query('nested', path='external_identifiers', query=(es.Q('match', identifier=ident) & es.Q('match', source=source)))
    if parent:
        q = q.query('match', parent=parent)
    res = q.execute()
    if len(res.hits) == 1:
        return res.hits[0]
    else:
        print("Got {} results, expected 1.".format(len(res.hits)))
        return False


def get_uri():
    return "uri"


def is_resolved(obj):
    if obj.meta.id:
        return True
    return False
