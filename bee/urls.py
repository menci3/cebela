from django.urls import path

from . import views

app_name = 'bee'
urlpatterns = [
    path('', views.index, name='index'),
    path('video_stream/', views.video_stream, name='video_stream'),
    path('tracking/', views.tracking_view, name='tracking_view'),
    path('tracking_stream/', views.tracking_stream, name='tracking_stream'),
    path('stats/', views.stats, name='stats'),
    path('settings/', views.settings_view, name='settings_view'),
    path('settings_update/', views.settings_update, name='settings_update'),
    path('tracking_start/', views.tracking_start, name='tracking_start'),
    path('tracking_stop/', views.tracking_stop, name='tracking_stop'),
    path('tracking_status/', views.tracking_status, name='tracking_status'),
    path('video_start/', views.video_start, name='video_start'),
    path('video_resume/', views.video_resume, name='video_resume'),
    path('video_stop/', views.video_stop, name='video_stop'),
]
