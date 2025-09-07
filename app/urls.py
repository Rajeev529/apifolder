from django.urls import path,include
from . import views, auth, createApi, crud, advocat
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path("", views.index),
    path("admin", views.admin),
    path("login", views.login),
    path("signup", views.signup),
    path("signup1", auth.signup1),
    path("logout", auth.logout),
    path("login1", auth.login1),
    path("apiform", views.apiform),
    path("uploadpage", views.upload_page),
    path("createapi", createApi.create_api),
    path("answer/<str:apiKey>/", createApi.answer),
    path("table", views.table),
    path("api2/<str:apiKey>/", views.api2, name='api2'),
    path("findval", views.findval),
    path("editprompt", crud.editprompt),
    path("edit/<str:apikey>/", crud.edit, name='edit'),
    path("deleteapi/<str:apikey>/", crud.deleteapi, name='deleteapi'),
    path("advocate/<str:apikey>/", views.advo),
    path("embed", advocat.embed),
    path("alltables", views.alltables),
    path("chatbot", advocat.chatbot),
    path("delchat/<str:apikey>/", crud.delchat, name='delchat'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
