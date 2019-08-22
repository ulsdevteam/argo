from elasticsearch_dsl import analyzer

# TODO: build these out as necessary

html_strip = analyzer(
    'html_strip',
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)
