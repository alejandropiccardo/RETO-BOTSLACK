from django.urls import path
from .views import slack_commands, slack_events

urlpatterns = [
    path("events/", slack_events, name="slack_events"),
    path('commands/', slack_commands, name='slack_commands'),
]
