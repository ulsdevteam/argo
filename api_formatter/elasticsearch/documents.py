# This avoids name collisions between Object class in elasticsearch_dsl and our Object Document class
import elasticsearch_dsl as es

from .analyzers import base_analyzer


class ExternalIdentifier(es.InnerDoc):
    source = es.Text()
    identifier = es.Text()


class Extent(es.InnerDoc):
    value = es.Float()
    type = es.Text()


class Date(es.InnerDoc):
    begin = es.Date()
    end = es.Date()
    expression = es.Text()
    type = es.Text()
    label = es.Text()


class Language(es.InnerDoc):
    expression = es.Text()
    identifier = es.Text()


class Subnote(es.InnerDoc):
    type = es.Text()
    content = es.Text(analyzer=base_analyzer)


class Note(es.InnerDoc):
    type = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    source = es.Text()
    subnotes = es.Object(Subnote)


class Reference(es.InnerDoc):
    title = es.Text(analyzer=base_analyzer)
    ref = es.Text()
    role = es.Text()
    external_identifiers = es.Nested(ExternalIdentifier)


class RightsGranted(es.InnerDoc):
    act = es.Text()
    dateStart = es.Date()
    dateEnd = es.Date()
    restriction = es.Text()
    notes = es.Nested(Note)


class RightsStatement(es.InnerDoc):
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
    id = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(fields={'keyword': es.Keyword()})
    dates = es.Object(Date)
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
    id = es.Text()
    title = es.Text(analyzer=base_analyzer, fields={'keyword': es.Keyword()})
    type = es.Text(fields={'keyword': es.Keyword()})
    external_identifiers = es.Nested(ExternalIdentifier)

    class Index:
        name = 'terms'
