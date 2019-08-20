from django.conf import settings
from elasticsearch_dsl import Date, Document, Float, InnerDoc, Index, Keyword, Nested, Text

from .analyzers import html_strip


class ExternalIdentifier(InnerDoc):
    source = Text()
    identifier = Text()


class Extent(InnerDoc):
    value = Float()
    type = Text()


class Date(InnerDoc):
    begin = Date()
    end = Date()
    expression = Text()
    type = Text()
    label = Text()


class Language(InnerDoc):
    expression = Text()
    identifier = Text()


class Subnote(InnerDoc):
    type = Text()
    content = Text(analyzer='snowball')


class Note(InnerDoc):
    type = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    source = Text()
    subnotes = Nested(Subnote)


class URI(InnerDoc):
    ref = Text()


class RightsGranted(InnerDoc):
    act = Text()
    dateStart = Date()
    dateEnd = Date()
    restriction = Text()
    notes = Nested(Note)


class RightsStatement(InnerDoc):
    determinationDate = Date()
    type = Text()
    rightsType = Text()
    dateStart = Date()
    dateEnd = Date()
    copyrightStatus = Text()
    otherBasis = Text()
    jurisdiction = Text()
    notes = Nested(Note)
    rights_granted = Nested(RightsGranted)


class Agent(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    description = Text(analyzer='snowball')
    type = Text()
    dates = Nested(Date)
    notes = Nested(Note)
    external_identifiers = Nested(ExternalIdentifier)

    class Index:
        name = 'agents'


class Collection(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text()
    level = Text()
    dates = Nested(Date)
    languages = Nested(Language)
    extents = Nested(Extent)
    notes = Nested(Note)
    rights_statements = Nested(RightsStatement)
    external_identifiers = Nested(ExternalIdentifier)
    agents = Nested(URI)  # TODO: do agents need a role?
    terms = Nested(URI)
    creators = Nested(URI)  # TODO: should this be part of agents?
    ancestors = Nested(URI)
    children = Nested(URI)

    class Index:
        name = 'collections'


class Object(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text()
    dates = Nested(Date)
    languages = Nested(Language)
    extents = Nested(Extent)
    notes = Nested(Note)
    rights_statements = Nested(RightsStatement)
    external_identifiers = Nested(ExternalIdentifier)
    agents = Nested(URI)  # TODO: do agents need a role?
    terms = Nested(URI)
    ancestors = Nested(URI)

    class Index:
        name = 'objects'


class Term(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text()
    external_identifiers = Nested(ExternalIdentifier)

    class Index:
        name = 'terms'
