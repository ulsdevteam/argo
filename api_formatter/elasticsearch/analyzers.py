from elasticsearch_dsl import analyzer, tokenizer

base_analyzer = analyzer(
    'base_analyzer',
    tokenizer=tokenizer("standard"),
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)
