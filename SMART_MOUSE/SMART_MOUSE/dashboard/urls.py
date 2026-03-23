from django.urls import path
from . import views

urlpatterns = [
    path('',                views.home,            name='home'),
    path('api/status/',     views.get_status,      name='status'),
    path('api/start/',      views.start_system,    name='start'),
    path('api/stop/',       views.stop_system,     name='stop'),
    path('api/settings/',   views.update_settings, name='settings'),
    path('api/video/',      views.video_feed,      name='video'),
]