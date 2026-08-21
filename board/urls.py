from django.urls import path

from . import views

app_name = 'board'

urlpatterns = [
    path('', views.board_home, name='home'),
    path('questions/new/', views.create_question, name='create_question'),
    path('questions/<int:question_id>/vote/', views.vote_question, name='vote_question'),
]
