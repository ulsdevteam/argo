# This avoids name collisions between Object class in elasticsearch_dsl and our Object Document class
import elasticsearch_dsl as es

from .analyzers import base_analyzer


class ExternalIdentifier(es.InnerDoc):
    """Abstract representation of external identifier object.
    Used on Documents to unambiguously tie them to source data.
    """
    source = es.Text()
    identifier = es.Text()


class Extent(es.InnerDoc):
    """Refers to the size of a group of records."""
    value = es.Float()
    type = es.Text()


class Date(es.InnerDoc):
    """Refers to a single date or date range.
    Used on Documents to create human and machine readable date representations.
    The `expression` field is intended to be a human readable representation of a date or date range,
    while the begin and end values are machine readable and actionable values.
    """
    begin = es.Date()
    end = es.Date()
    expression = es.Text()
    type = es.Text()
    label = es.Text()


class Language(es.InnerDoc):
    """Refers to a human language."""
    expression = es.Text()
    identifier = es.Text()


class Subnote(es.InnerDoc):
    """Abstract wrapper for note content, associated with Note Documents."""
    type = es.Text()
    content = es.Text(analyzer=base_analyzer)


class Note(es.InnerDoc):
    """Abstract representation of notes, which are typed and contain human readable
    content in a Subnotes InnerDoc.
    """
    type = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    source = es.Text()
    subnotes = es.Object(Subnote)


class Reference(es.InnerDoc):
    """Abstract reference to a Document, which likely exists in a different index.
    On initial indexing, reference may only consist of an external_identifiers array,
    but additional data will likely be added during indexing.
    """
    title = es.Text(analyzer=base_analyzer)
    uri = es.Text()
    type = es.Text()
    order = es.Integer()
    external_identifiers = es.Nested(ExternalIdentifier)


class RightsGranted(es.InnerDoc):
    """Abstract wrapper for RightsGranted information, associated with a RightsStatement Document."""
    act = es.Text()
    dateStart = es.Date()
    dateEnd = es.Date()
    restriction = es.Text()
    notes = es.Nested(Note)


class RightsStatement(es.InnerDoc):
    """Machine readable representation of restrictions or permissions,
    generally related to a group of archival records. This structure is based
    on the PREservation Metadata: Implementation Strategies (PREMIS) Rights entity.
    """
    determinationDate = es.Date()
    type = es.Text()
    rightsType = es.Text()
    dateStart = es.Date()
    dateEnd = es.Date()
    copyrightStatus = es.Text()
    otherBasis = es.Text()
    jurisdiction = es.Text()
    notes = es.Nested(Note)
    rights_granted = es.Nested(RightsGranted)


class Agent(es.Document):
    """A person, organization or family that was involved in the creation and
    maintenance of records, or is the subject of those records.
    """
    id = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    description = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
    notes = es.Nested(Note)
    external_identifiers = es.Nested(ExternalIdentifier)

    class Index:
        name = 'agents'


class Collection(es.Document):
    """A group of archival records which contains other groups of records,
    and may itself be part of a larger Collection.  Collections are not
    physical groups of records, such as boxes and folders, but are intellectually
    significant aggregations which crucial to understanding the context of
    records creation and maintenance, such as record groups or series.
    """
    id = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(fields={'keyword': es.Keyword()})
    level = es.Text(fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
    languages = es.Object(Language)
    notes = es.Nested(Note)
    extents = es.Nested(Extent)
    rights_statements = es.Nested(RightsStatement)
    external_identifiers = es.Nested(ExternalIdentifier)
    agents = es.Nested(Reference)
    terms = es.Nested(Reference)
    creators = es.Nested(Reference)  # TODO: should this be part of agents?
    ancestors = es.Nested(Reference)
    children = es.Nested(Reference)

    class Index:
        name = 'collections'


class Object(es.Document):
    """A group of archival records which is part of a larger Collection,
    but does not contain any other aggregations.
    """
    id = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(fields={'keyword': es.Keyword()})
    dates = es.Object(Date, )
    languages = es.Object(Language)
    extents = es.Nested(Extent)
    notes = es.Nested(Note)
    rights_statements = es.Nested(RightsStatement)
    external_identifiers = es.Nested(ExternalIdentifier)
    agents = es.Nested(Reference)
    terms = es.Nested(Reference)
    ancestors = es.Nested(Reference)

    class Index:
        name = 'objects'


class Term(es.Document):
    """A controlled term topical, geo"""
    id = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(fields={'keyword': es.Keyword()})
    external_identifiers = es.Nested(ExternalIdentifier)

    class Index:
        name = 'terms'
