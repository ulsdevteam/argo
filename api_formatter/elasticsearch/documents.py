from django.conf import settings
from elasticsearch_dsl import Date, Document, InnerDoc, Index, Keyword, Nested, Text

from .analyzers import html_strip


class ExternalIdentifier(InnerDoc):
    source = Text()
    identififier = Text()


class Date(InnerDoc):
    begin = Date()
    end = Date()
    expression = Text()
    type = Text()
    label = Text()


class Subnote(InnerDoc):
    type = Text()
    content = Text(analyzer='snowball')


class Note(InnerDoc):
    type = Text()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    source = Text()
    subnotes = Nested(Subnote)


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
