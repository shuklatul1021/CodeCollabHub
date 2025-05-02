from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/projects/(?P<project_id>\d+)/files/(?P<file_id>\d+)/$', consumers.CodeEditorConsumer.as_asgi()),
]
