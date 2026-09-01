import os
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
import qrcode

from .models import Board, Question, Vote
from .theme import THEME_COOKIE_NAME, get_safe_redirect_target, normalize_theme


VOTER_COOKIE_NAME = 'board_voter'
OWNER_BOARDS_PAGE_SIZE = 12
OWNER_TAB_QUESTIONS_PAGE_SIZE = 20
PUBLIC_QUESTIONS_PAGE_SIZE = 20
QUESTION_TEXT_LIMIT = 160
QUESTION_DEFAULT_NICKNAME = 'Anonymous'


def _paginate_request_queryset(request, queryset, page_size, page_param='page'):
    paginator = Paginator(queryset, page_size)
    return paginator.get_page(request.GET.get(page_param) or 1)


def _get_or_create_voter_token(request):
    token = request.COOKIES.get(VOTER_COOKIE_NAME)
    if not token:
        token = os.urandom(16).hex()
    return token


def _build_question_form_state(request):
    return {
        'question_form_nickname': (request.POST.get('nickname') or '').strip(),
        'question_form_text': (request.POST.get('text') or '').strip(),
        'question_text_limit': QUESTION_TEXT_LIMIT,
    }


def _style_auth_form(form):
    for field in form.visible_fields():
        widget = field.field.widget
        input_type = getattr(widget, 'input_type', '')
        if input_type == 'checkbox':
            classes = 'checkbox checkbox-primary'
        else:
            classes = 'input input-bordered w-full'

        if form.is_bound and field.errors:
            classes += ' input-error'
            widget.attrs['aria-invalid'] = 'true'

        widget.attrs['class'] = classes
        widget.attrs.setdefault('autocomplete', field.name)


def landing_page(request):
    return render(request, 'board/landing.html')


def set_theme(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:landing'))

    theme = normalize_theme(request.POST.get('theme', ''))
    next_url = get_safe_redirect_target(request, reverse('board:landing'))
    response = HttpResponseRedirect(next_url)
    response.set_cookie(THEME_COOKIE_NAME, theme, max_age=60 * 60 * 24 * 365)
    return response


def join_by_code(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:landing'))

    code = (request.POST.get('code') or '').strip().lower()
    if not code:
        messages.error(request, 'Enter a board code to join.')
        return HttpResponseRedirect(reverse('board:landing'))

    board = Board.objects.filter(code=code).first()
    if not board:
        messages.error(request, 'Board code not found. Check the code and try again.')
        return HttpResponseRedirect(reverse('board:landing'))

    return HttpResponseRedirect(reverse('board:home', args=[board.code]))


def sign_up(request):
    form = UserCreationForm(request.POST or None)
    _style_auth_form(form)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return HttpResponseRedirect(reverse('board:owner_boards'))
    return render(request, 'board/auth/sign_up.html', {'form': form})


def sign_in(request):
    form = AuthenticationForm(request, data=request.POST or None)
    _style_auth_form(form)
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
    boards_page = _paginate_request_queryset(request, boards, OWNER_BOARDS_PAGE_SIZE)
    return render(request, 'board/owner/boards_list.html', {
        'boards': boards_page.object_list,
        'boards_page': boards_page,
    })


@login_required
def owner_board_new(request):
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        if title:
            board = Board.objects.create(title=title, owner=request.user)
            return HttpResponseRedirect(reverse('board:owner_board_detail', args=[board.id]))
        messages.error(request, 'Board title is required.')
        return render(request, 'board/owner/board_new.html', {
            'title_value': title,
            'title_error': True,
        })
    return render(request, 'board/owner/board_new.html', {
        'title_value': '',
        'title_error': False,
    })


@login_required
def owner_board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    active_qs = board.questions.filter(state=Question.STATE_ACTIVE)
    hidden_qs = board.questions.filter(state=Question.STATE_HIDDEN)
    archived_qs = board.questions.filter(state=Question.STATE_ARCHIVED)

    selected_tab = request.GET.get('tab', Question.STATE_ACTIVE)
    tab_map = {
        Question.STATE_ACTIVE: active_qs,
        Question.STATE_HIDDEN: hidden_qs,
        Question.STATE_ARCHIVED: archived_qs,
    }
    if selected_tab not in tab_map:
        selected_tab = Question.STATE_ACTIVE

    tab_questions_page = _paginate_request_queryset(
        request,
        tab_map[selected_tab],
        OWNER_TAB_QUESTIONS_PAGE_SIZE,
    )

    context = {
        'board': board,
        'active_count': active_qs.count(),
        'hidden_count': hidden_qs.count(),
        'archived_count': archived_qs.count(),
        'selected_tab': selected_tab,
        'tab_questions': tab_questions_page.object_list,
        'tab_questions_page': tab_questions_page,
    }
    return render(request, 'board/owner/board_detail.html', context)


@login_required
def owner_moderate_question(request, board_id, question_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:owner_board_detail', args=[board.id]))

    question = get_object_or_404(Question, pk=question_id, board=board)
    new_state = request.POST.get('state', '')
    valid_states = {Question.STATE_ACTIVE, Question.STATE_HIDDEN, Question.STATE_ARCHIVED}
    if new_state in valid_states:
        try:
            question.transition_to(new_state)
        except ValueError:
            pass
    return HttpResponseRedirect(reverse('board:owner_board_detail', args=[board.id]))


@login_required
def owner_close_board(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    if request.method == 'POST' and board.status != Board.STATUS_CLOSED:
        board.status = Board.STATUS_CLOSED
        board.save(update_fields=['status', 'updated_at'])
    return HttpResponseRedirect(reverse('board:owner_board_detail', args=[board.id]))


@login_required
def owner_board_qr(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    qr = qrcode.QRCode(version=1, box_size=12, border=2)
    qr.add_data(board.get_public_url(request))
    qr.make(fit=True)

    image = qr.make_image(fill_color='black', back_color='white')
    output = BytesIO()
    image.save(output, format='PNG')

    response = HttpResponse(output.getvalue(), content_type='image/png')
    if request.GET.get('download') == '1':
        response['Content-Disposition'] = f'attachment; filename="board-{board.code}.png"'
    return response


def board_home_redesign_prototype(request, board_code):
    board = get_object_or_404(Board, code=board_code)
    requested_theme = (request.GET.get('theme') or 'light').lower()
    theme = requested_theme if requested_theme in {'light', 'dark'} else 'light'
    questions = [
        {
            'nickname': 'Anonymous',
            'initial': 'A',
            'time_label': '12 hours ago',
            'text': 'What do you think of BND?',
            'votes': 0,
            'featured': True,
            'status_label': 'Needs review',
            'host_note': {
                'author': 'Moderator',
                'time_label': '12 hours ago',
                'text': 'Best spidey movie yet. IMO',
            },
        },
        {
            'nickname': 'dani97',
            'initial': 'D',
            'time_label': '12 hours ago',
            'text': 'Your thoughts on the succession series!',
            'votes': 2,
            'featured': False,
            'status_label': 'Trending',
            'host_note': None,
        },
        {
            'nickname': 'Anonymous',
            'initial': 'A',
            'time_label': '12 hours ago',
            'text': 'What movies are trending lately?',
            'votes': 0,
            'featured': False,
            'status_label': 'New',
            'host_note': {
                'author': 'Host',
                'time_label': 'Moments ago',
                'text': 'Collecting recommendations for the closing slide.',
            },
        },
    ]

    context = {
        'board': board,
        'theme': theme,
        'is_dark_theme': theme == 'dark',
        'question_count': len(questions),
        'response_count': sum(1 for question in questions if question['host_note']),
        'participant_count': 175,
        'questions': questions,
    }
    return render(request, 'board/home_prototype_redesign.html', context)


def board_home(request, board_code):
    board = get_object_or_404(Board, code=board_code)
    questions = board.questions.filter(state=Question.STATE_ACTIVE).order_by('-vote_count', '-created_at', '-id')
    questions_page = _paginate_request_queryset(request, questions, PUBLIC_QUESTIONS_PAGE_SIZE)
    voter_token = request.COOKIES.get(VOTER_COOKIE_NAME)
    voted_ids = set(
        Vote.objects.filter(voter_token=voter_token, question__in=questions_page.object_list).values_list('question_id', flat=True)
    ) if voter_token else set()
    is_owner = request.user.is_authenticated and board.owner_id == request.user.id
    context = {
        'board': board,
        'questions': questions_page.object_list,
        'questions_page': questions_page,
        'voted_ids': voted_ids,
        'public_url': board.get_public_url(request),
        'is_owner': is_owner,
    }
    context.update(_build_question_form_state(request))
    if request.headers.get('HX-Request'):
        return render(request, 'board/partials/question_list.html', context)
    return render(request, 'board/home.html', context)


def create_question(request, board_code):
    board = get_object_or_404(Board, code=board_code)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    if board.status != Board.STATUS_ACTIVE:
        messages.error(request, 'This board is closed. New questions are disabled.')
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    nickname = (request.POST.get('nickname') or '').strip()
    text = (request.POST.get('text') or '').strip()

    if len(nickname) > 50:
        messages.error(request, 'Nickname must be 50 characters or fewer.')
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))
    if len(text) > QUESTION_TEXT_LIMIT:
        messages.error(request, f'Question must be {QUESTION_TEXT_LIMIT} characters or fewer.')
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))
    if not text:
        messages.error(request, 'Question text is required.')
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    Question.objects.create(
        board=board,
        nickname=nickname or QUESTION_DEFAULT_NICKNAME,
        text=text,
    )
    messages.success(request, 'Your question was added.')

    return HttpResponseRedirect(reverse('board:home', args=[board.code]))


def vote_question(request, board_code, question_id):
    board = get_object_or_404(Board, code=board_code)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('board:home', args=[board.code]))

    if board.status != Board.STATUS_ACTIVE:
        messages.error(request, 'This board is closed. Voting is disabled.')
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('board:home', args=[board.code])
            return response
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
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('board:home', args=[board.code])
        response.set_cookie(VOTER_COOKIE_NAME, voter_token, max_age=60 * 60 * 24 * 365)
        return response

    response = HttpResponseRedirect(reverse('board:home', args=[board.code]))
    response.set_cookie(VOTER_COOKIE_NAME, voter_token, max_age=60 * 60 * 24 * 365)
    return response


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)
