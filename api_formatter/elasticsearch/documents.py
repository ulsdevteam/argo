from django.conf import settings
from elasticsearch_dsl import Date, Document, Float, InnerDoc, Index, Keyword, Object, Text

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
    subnotes = Object(Subnote)


class URI(InnerDoc):
    ref = Text()


class RightsGranted(InnerDoc):
    act = Text()
    dateStart = Date()
    dateEnd = Date()
    restriction = Text()
    notes = Object(Note)


class RightsStatement(InnerDoc):
    determinationDate = Date()
    type = Text()
    rightsType = Text()
    dateStart = Date()
    dateEnd = Date()
    copyrightStatus = Text()
    otherBasis = Text()
    jurisdiction = Text()
    notes = Object(Note)
    rights_granted = Object(RightsGranted)


class Agent(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    description = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text(fields={'raw': Keyword()})
    dates = Object(Date)
    notes = Object(Note)
    external_identifiers = Object(ExternalIdentifier)

    class Index:
        name = 'agents'


class Collection(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text(fields={'raw': Keyword()})
    level = Text()
    dates = Object(Date)
    languages = Object(Language)
    extents = Object(Extent)
    notes = Object(Note)
    rights_statements = Object(RightsStatement)
    external_identifiers = Object(ExternalIdentifier)
    agents = Object(URI)  # TODO: do agents need a role?
    terms = Object(URI)
    creators = Object(URI)  # TODO: should this be part of agents?
    ancestors = Object(URI)
    children = Object(URI)

    class Index:
        name = 'collections'


class Object(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text(fields={'raw': Keyword()})
    dates = Object(Date)
    languages = Object(Language)
    extents = Object(Extent)
    notes = Object(Note)
    rights_statements = Object(RightsStatement)
    external_identifiers = Object(ExternalIdentifier)
    agents = Object(URI)  # TODO: do agents need a role?
    terms = Object(URI)
    ancestors = Object(URI)

    class Index:
        name = 'objects'


class Term(Document):
    id = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    type = Text()
    # external_identifiers = Object(ExternalIdentifier)

    class Index:
        name = 'terms'
