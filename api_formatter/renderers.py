from rest_framework import renderers


class CharsetJSONRenderer(renderers.JSONRenderer):
    charset = 'utf-8'
