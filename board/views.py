import os

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Board, Question, Vote


VOTER_COOKIE_NAME = 'board_voter'


def _get_or_create_voter_token(request):
    token = request.COOKIES.get(VOTER_COOKIE_NAME)
    if not token:
        token = os.urandom(16).hex()
    return token


def landing_page(request):
    boards = Board.objects.filter(status=Board.STATUS_ACTIVE).order_by('-created_at', '-id')
    return render(request, 'board/landing.html', {'boards': boards})


def sign_up(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return HttpResponseRedirect(reverse('board:owner_boards'))
    return render(request, 'board/auth/sign_up.html', {'form': form})


def sign_in(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return HttpResponseRedirect(reverse('board:owner_boards'))
    return render(request, 'board/auth/sign_in.html', {'form': form})


@login_required
def sign_out(request):
    if request.method == 'POST':
        logout(request)
    return HttpResponseRedirect(reverse('board:landing'))


@login_required
def owner_boards(request):
    boards = Board.objects.filter(owner=request.user).order_by('-created_at', '-id')
    return render(request, 'board/owner/boards_list.html', {'boards': boards})


@login_required
def owner_board_new(request):
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        if title:
            board = Board.objects.create(title=title, owner=request.user)
            return HttpResponseRedirect(reverse('board:owner_board_detail', args=[board.id]))
        messages.error(request, 'Board title is required.')
    return render(request, 'board/owner/board_new.html')


@login_required
def owner_board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    return render(request, 'board/owner/board_detail.html', {'board': board})


def board_home(request, board_code):
    board = get_object_or_404(Board, code=board_code)
    questions = board.questions.filter(state=Question.STATE_ACTIVE).order_by('-vote_count', '-created_at', '-id')
    voter_token = request.COOKIES.get(VOTER_COOKIE_NAME)
    voted_ids = set(
        Vote.objects.filter(voter_token=voter_token, question__board=board).values_list('question_id', flat=True)
    ) if voter_token else set()
    context = {'board': board, 'questions': questions, 'voted_ids': voted_ids}
    if request.headers.get('HX-Request'):
        return render(request, 'board/partials/question_list.html', context)
    return render(request, 'board/home.html', context)


def create_question(request, board_code):
    board = get_object_or_404(Board, code=board_code)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    nickname = (request.POST.get('nickname') or '').strip()
    text = (request.POST.get('text') or '').strip()

    if len(nickname) > 50:
        messages.error(request, 'Nickname must be 50 characters or fewer.')
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))
    if len(text) > 500:
        messages.error(request, 'Question must be 500 characters or fewer.')
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    if nickname and text:
        Question.objects.create(board=board, nickname=nickname, text=text)
        messages.success(request, 'Your question was added.')

    return HttpResponseRedirect(reverse('board:home', args=[board.code]))


def vote_question(request, board_code, question_id):
    board = get_object_or_404(Board, code=board_code)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    voter_token = _get_or_create_voter_token(request)
    question = get_object_or_404(Question, pk=question_id, board=board)

    try:
        with transaction.atomic():
            Vote.objects.create(question=question, voter_token=voter_token)
            question.vote_count += 1
            question.save(update_fields=['vote_count', 'updated_at'])
    except IntegrityError:
        messages.error(request, 'You already voted on this question.')

    if request.headers.get('HX-Request'):
        from django.http import HttpResponse
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('board:home', args=[board.code])
        response.set_cookie(VOTER_COOKIE_NAME, voter_token, max_age=60 * 60 * 24 * 365)
        return response

    response = HttpResponseRedirect(reverse('board:home', args=[board.code]))
    response.set_cookie(VOTER_COOKIE_NAME, voter_token, max_age=60 * 60 * 24 * 365)
    return response


@staff_member_required
def manage_board(request):
    active = Question.objects.filter(state=Question.STATE_ACTIVE)
    hidden = Question.objects.filter(state=Question.STATE_HIDDEN)
    archived = Question.objects.filter(state=Question.STATE_ARCHIVED)
    return render(request, 'board/manage.html', {
        'active': active,
        'hidden': hidden,
        'archived': archived,
    })


@staff_member_required
def moderate_question(request, question_id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:manage'))
    question = get_object_or_404(Question, pk=question_id)
    new_state = request.POST.get('state', '')
    valid_states = {Question.STATE_ACTIVE, Question.STATE_HIDDEN, Question.STATE_ARCHIVED}
    if new_state in valid_states:
        try:
            question.transition_to(new_state)
        except ValueError:
            pass
    return HttpResponseRedirect(reverse('board:manage'))
