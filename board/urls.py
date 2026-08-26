from django.urls import path

from . import views

app_name = 'board'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('b/<str:board_code>/', views.board_home, name='home'),
    path('b/<str:board_code>/questions/new/', views.create_question, name='create_question'),
    path('b/<str:board_code>/questions/<int:question_id>/vote/', views.vote_question, name='vote_question'),
    path('manage/', views.manage_board, name='manage'),
    path('manage/questions/<int:question_id>/state/', views.moderate_question, name='moderate_question'),
]
