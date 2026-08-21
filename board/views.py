import os

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Question, Vote


VOTER_COOKIE_NAME = 'board_voter'


def _get_or_create_voter_token(request):
    token = request.COOKIES.get(VOTER_COOKIE_NAME)
    if not token:
        token = os.urandom(16).hex()
    return token


def board_home(request):
    questions = Question.objects.filter(state=Question.STATE_ACTIVE).order_by('-vote_count', '-created_at', '-id')
    voter_token = request.COOKIES.get(VOTER_COOKIE_NAME)
    voted_ids = set(
        Vote.objects.filter(voter_token=voter_token).values_list('question_id', flat=True)
    ) if voter_token else set()
    return render(request, 'board/home.html', {'questions': questions, 'voted_ids': voted_ids})


def create_question(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home'))

    nickname = (request.POST.get('nickname') or '').strip()
    text = (request.POST.get('text') or '').strip()

    if len(nickname) > 50:
        messages.error(request, 'Nickname must be 50 characters or fewer.')
        return HttpResponseRedirect(reverse('board:home'))
    if len(text) > 500:
        messages.error(request, 'Question must be 500 characters or fewer.')
        return HttpResponseRedirect(reverse('board:home'))

    if nickname and text:
        Question.objects.create(nickname=nickname, text=text)
        messages.success(request, 'Your question was added.')

    return HttpResponseRedirect(reverse('board:home'))


def vote_question(request, question_id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home'))

    voter_token = _get_or_create_voter_token(request)
    question = get_object_or_404(Question, pk=question_id)

    try:
        with transaction.atomic():
            Vote.objects.create(question=question, voter_token=voter_token)
            question.vote_count += 1
            question.save(update_fields=['vote_count', 'updated_at'])
    except IntegrityError:
        messages.error(request, 'You already voted on this question.')

    response = HttpResponseRedirect(reverse('board:home'))
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
