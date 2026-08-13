from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("chat/",views.chat_view,name = "chat"),
    path("documents/<int:document_id>/delete/",views.delete_document,name="delete_document",),
]