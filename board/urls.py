from django.urls import path

from . import views

app_name = 'board'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('accounts/sign-up/', views.sign_up, name='sign_up'),
    path('accounts/sign-in/', views.sign_in, name='sign_in'),
    path('accounts/sign-out/', views.sign_out, name='sign_out'),
    path('boards/', views.owner_boards, name='owner_boards'),
    path('boards/new/', views.owner_board_new, name='owner_board_new'),
    path('boards/<int:board_id>/', views.owner_board_detail, name='owner_board_detail'),
    path('b/<str:board_code>/', views.board_home, name='home'),
    path('b/<str:board_code>/questions/new/', views.create_question, name='create_question'),
    path('b/<str:board_code>/questions/<int:question_id>/vote/', views.vote_question, name='vote_question'),
    path('manage/', views.manage_board, name='manage'),
    path('manage/questions/<int:question_id>/state/', views.moderate_question, name='moderate_question'),
]
