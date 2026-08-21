import os

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
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
    return render(request, 'board/home.html', {'questions': questions})


def create_question(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home'))

    nickname = (request.POST.get('nickname') or '').strip()
    text = (request.POST.get('text') or '').strip()

    if nickname and text:
        Question.objects.create(nickname=nickname, text=text)
        messages.success(request, 'Your question was added.')

    return HttpResponseRedirect(reverse('board:home'))


def vote_question(request, question_id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home'))

    voter_token = _get_or_create_voter_token(request)
    question = Question.objects.get(pk=question_id)

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
