from elasticsearch_dsl import connections, Index, Q, Search

from .documents import *


def resolve_reference(obj, sources, doc_cls):
    ident = [i.identifier for i in obj.external_identifiers if obj.source == source][0]
    primary_doc = document_by_external_id(doc_cls, ident, source)
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
    search = Search(
        using=self.client,
        index=doc_cls._index._name,
        doc_type=doc_cls._doc_type.name
    )
    q = search.query('nested', path='external_identifiers', query=(Q('match', identifier=ident) & Q('match', source=source)))
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
