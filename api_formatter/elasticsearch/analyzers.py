from elasticsearch_dsl import analyzer

html_strip = analyzer(
    'base_analyzer',
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)
