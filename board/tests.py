from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Board, Question, Vote


class BoardScopedTests(TestCase):
    def setUp(self):
        self.board = Board.objects.create(title='Demo Board')
        self.other_board = Board.objects.create(title='Other Board')


class QuestionBoardTests(BoardScopedTests):
    def test_create_question_and_list_it(self):
        response = self.client.post(
            reverse('board:create_question', args=[self.board.code]),
            {'nickname': 'Alice', 'text': 'Can we add question sorting?'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Question.objects.get().nickname, 'Alice')
        self.assertEqual(Question.objects.get().board, self.board)

    def test_questions_are_ordered_by_votes_then_newest(self):
        first = Question.objects.create(board=self.board, nickname='one', text='First', vote_count=1)
        second = Question.objects.create(board=self.board, nickname='two', text='Second', vote_count=3)
        third = Question.objects.create(board=self.board, nickname='three', text='Third', vote_count=3)

        qs = list(Question.objects.order_by('-vote_count', '-created_at', '-id'))
        self.assertEqual(qs[0].id, third.id)
        self.assertEqual(qs[1].id, second.id)
        self.assertEqual(qs[2].id, first.id)

    def test_same_browser_can_only_vote_once_per_question(self):
        question = Question.objects.create(board=self.board, nickname='Host', text='Test question')
        response = self.client.post(
            reverse('board:vote_question', args=[self.board.code, question.pk]),
            HTTP_COOKIE='board_voter=abc123'
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(question.votes.count(), 1)

        second_response = self.client.post(
            reverse('board:vote_question', args=[self.board.code, question.pk]),
            HTTP_COOKIE='board_voter=abc123'
        )

        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(question.votes.count(), 1)

    def test_board_home_shows_only_questions_for_target_board(self):
        in_board = Question.objects.create(board=self.board, nickname='Alice', text='Visible')
        out_board = Question.objects.create(board=self.other_board, nickname='Bob', text='Hidden elsewhere')

        response = self.client.get(reverse('board:home', args=[self.board.code]))

        self.assertIn(in_board, response.context['questions'])
        self.assertNotIn(out_board, response.context['questions'])

    def test_landing_page_lists_available_boards(self):
        response = self.client.get(reverse('board:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.board.title)
        self.assertContains(response, self.other_board.title)


class EnvHardeningTests(BoardScopedTests):
    def test_vote_on_missing_question_returns_404(self):
        response = self.client.post(reverse('board:vote_question', args=[self.board.code, 99999]))
        self.assertEqual(response.status_code, 404)

    def test_create_question_rejects_long_nickname(self):
        response = self.client.post(
            reverse('board:create_question', args=[self.board.code]),
            {'nickname': 'x' * 51, 'text': 'Valid question text'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Question.objects.count(), 0)

    def test_create_question_rejects_long_text(self):
        response = self.client.post(
            reverse('board:create_question', args=[self.board.code]),
            {'nickname': 'Alice', 'text': 'x' * 501}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Question.objects.count(), 0)


class UIPolishTests(BoardScopedTests):
    def test_board_home_includes_voted_ids_in_context(self):
        Question.objects.create(board=self.board, nickname='Alice', text='Test question')
        response = self.client.get(reverse('board:home', args=[self.board.code]), HTTP_COOKIE='board_voter=tok1')
        self.assertIn('voted_ids', response.context)

    def test_voted_question_id_present_in_voted_ids(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test question')
        Vote.objects.create(question=question, voter_token='tok1')
        response = self.client.get(reverse('board:home', args=[self.board.code]), HTTP_COOKIE='board_voter=tok1')
        self.assertIn(question.id, response.context['voted_ids'])

    def test_unvoted_question_id_absent_from_voted_ids(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test question')
        response = self.client.get(reverse('board:home', args=[self.board.code]), HTTP_COOKIE='board_voter=tok1')
        self.assertNotIn(question.id, response.context['voted_ids'])

    def test_no_voter_cookie_gives_empty_voted_ids(self):
        Question.objects.create(board=self.board, nickname='Alice', text='Test question')
        response = self.client.get(reverse('board:home', args=[self.board.code]))
        self.assertEqual(response.context['voted_ids'], set())

    def test_voted_ids_ignore_votes_from_other_boards(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Visible')
        other_question = Question.objects.create(board=self.other_board, nickname='Bob', text='Other')
        Vote.objects.create(question=other_question, voter_token='tok1')

        response = self.client.get(reverse('board:home', args=[self.board.code]), HTTP_COOKIE='board_voter=tok1')

        self.assertNotIn(question.id, response.context['voted_ids'])


class ModerationTests(BoardScopedTests):
    def setUp(self):
        super().setUp()
        self.owner = get_user_model().objects.create_user(username='owner1', password='owner-pass-123')
        self.other_owner = get_user_model().objects.create_user(username='owner2', password='owner-pass-456')
        self.board.owner = self.owner
        self.board.save(update_fields=['owner', 'updated_at'])
        self.other_board.owner = self.other_owner
        self.other_board.save(update_fields=['owner', 'updated_at'])

    def test_owner_moderation_requires_login(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test')
        response = self.client.post(
            reverse('board:owner_moderate_question', args=[self.board.id, question.pk]),
            {'state': 'hidden'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('board:sign_in'), response['Location'])

    def test_owner_can_hide_active_question(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test')
        self.client.login(username='owner1', password='owner-pass-123')
        self.client.post(
            reverse('board:owner_moderate_question', args=[self.board.id, question.pk]),
            {'state': 'hidden'}
        )
        question.refresh_from_db()
        self.assertEqual(question.state, Question.STATE_HIDDEN)

    def test_hidden_question_absent_from_participant_board(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test', state=Question.STATE_HIDDEN)
        response = self.client.get(reverse('board:home', args=[self.board.code]))
        self.assertNotIn(question, response.context['questions'])

    def test_invalid_transition_is_a_noop(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test', state=Question.STATE_ARCHIVED)
        self.client.login(username='owner1', password='owner-pass-123')
        self.client.post(
            reverse('board:owner_moderate_question', args=[self.board.id, question.pk]),
            {'state': 'hidden'}
        )
        question.refresh_from_db()
        self.assertEqual(question.state, Question.STATE_ARCHIVED)

    def test_owner_can_restore_archived_to_active(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test', state=Question.STATE_ARCHIVED)
        self.client.login(username='owner1', password='owner-pass-123')
        self.client.post(
            reverse('board:owner_moderate_question', args=[self.board.id, question.pk]),
            {'state': 'active'}
        )
        question.refresh_from_db()
        self.assertEqual(question.state, Question.STATE_ACTIVE)

    def test_owner_cannot_moderate_other_owner_board(self):
        question = Question.objects.create(board=self.other_board, nickname='Bob', text='Other board question')
        self.client.login(username='owner1', password='owner-pass-123')

        response = self.client.post(
            reverse('board:owner_moderate_question', args=[self.other_board.id, question.pk]),
            {'state': 'hidden'}
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_cannot_moderate_question_outside_board_route(self):
        question = Question.objects.create(board=self.other_board, nickname='Bob', text='Other board question')
        self.client.login(username='owner1', password='owner-pass-123')

        response = self.client.post(
            reverse('board:owner_moderate_question', args=[self.board.id, question.pk]),
            {'state': 'hidden'}
        )

        self.assertEqual(response.status_code, 404)


class HTMXVoteTests(BoardScopedTests):
    def test_standard_get_returns_full_page_template(self):
        response = self.client.get(reverse('board:home', args=[self.board.code]))
        self.assertTemplateUsed(response, 'board/home.html')

    def test_htmx_get_returns_partial_template(self):
        response = self.client.get(reverse('board:home', args=[self.board.code]), HTTP_HX_REQUEST='true')
        self.assertTemplateUsed(response, 'board/partials/question_list.html')
        self.assertTemplateNotUsed(response, 'board/home.html')

    def test_htmx_vote_returns_hx_redirect_header(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test question')
        response = self.client.post(
            reverse('board:vote_question', args=[self.board.code, question.pk]),
            HTTP_HX_REQUEST='true'
        )
        self.assertIn('HX-Redirect', response)
        self.assertEqual(response['HX-Redirect'], reverse('board:home', args=[self.board.code]))

    def test_standard_vote_returns_302(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test question')
        response = self.client.post(reverse('board:vote_question', args=[self.board.code, question.pk]))
        self.assertEqual(response.status_code, 302)

    def test_public_board_includes_polling_attributes(self):
        response = self.client.get(reverse('board:home', args=[self.board.code]))
        self.assertContains(response, 'hx-trigger="every 5s"')
        self.assertContains(response, f'hx-get="{reverse("board:home", args=[self.board.code])}"')

    def test_htmx_partial_preserves_polling_attributes(self):
        response = self.client.get(reverse('board:home', args=[self.board.code]), HTTP_HX_REQUEST='true')
        self.assertContains(response, 'hx-trigger="every 5s"')
        self.assertContains(response, f'hx-get="{reverse("board:home", args=[self.board.code])}"')

    def test_htmx_partial_polling_is_scoped_to_target_board(self):
        response = self.client.get(reverse('board:home', args=[self.other_board.code]), HTTP_HX_REQUEST='true')
        self.assertContains(response, f'hx-get="{reverse("board:home", args=[self.other_board.code])}"')


class OwnerAuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='owner1', password='owner-pass-123')

    def test_sign_up_creates_user_and_redirects_to_owner_boards(self):
        response = self.client.post(reverse('board:sign_up'), {
            'username': 'newowner',
            'password1': 'owner-pass-12345',
            'password2': 'owner-pass-12345',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='newowner').exists())
        self.assertRedirects(response, reverse('board:owner_boards'))

    def test_sign_in_redirects_to_owner_boards(self):
        response = self.client.post(reverse('board:sign_in'), {
            'username': 'owner1',
            'password': 'owner-pass-123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('board:owner_boards'))

    def test_owner_boards_requires_login(self):
        response = self.client.get(reverse('board:owner_boards'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('board:sign_in'), response['Location'])

    def test_owner_can_create_board(self):
        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.post(reverse('board:owner_board_new'), {'title': 'Townhall'})

        self.assertEqual(response.status_code, 302)
        board = Board.objects.get(title='Townhall')
        self.assertEqual(board.owner, self.user)
        self.assertRedirects(response, reverse('board:owner_board_detail', args=[board.id]))

    def test_owner_boards_lists_only_owned_boards(self):
        other_user = get_user_model().objects.create_user(username='owner2', password='owner-pass-456')
        own_board = Board.objects.create(title='My Board', owner=self.user)
        Board.objects.create(title='Other Board', owner=other_user)

        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.get(reverse('board:owner_boards'))

        self.assertContains(response, own_board.title)
        self.assertNotContains(response, 'Other Board')

    def test_owner_cannot_access_other_owner_board_detail(self):
        other_user = get_user_model().objects.create_user(username='owner2', password='owner-pass-456')
        other_board = Board.objects.create(title='Other Board', owner=other_user)

        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.get(reverse('board:owner_board_detail', args=[other_board.id]))

        self.assertEqual(response.status_code, 404)


class BoardCloseStateTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='owner1', password='owner-pass-123')
        self.other_owner = get_user_model().objects.create_user(username='owner2', password='owner-pass-456')
        self.board = Board.objects.create(title='Owner Board', owner=self.owner)
        self.other_board = Board.objects.create(title='Other Board', owner=self.other_owner)

    def test_owner_can_close_board(self):
        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.post(reverse('board:owner_close_board', args=[self.board.id]))

        self.assertEqual(response.status_code, 302)
        self.board.refresh_from_db()
        self.assertEqual(self.board.status, Board.STATUS_CLOSED)

    def test_owner_cannot_close_other_owner_board(self):
        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.post(reverse('board:owner_close_board', args=[self.other_board.id]))
        self.assertEqual(response.status_code, 404)

    def test_closed_board_rejects_question_creation(self):
        self.board.status = Board.STATUS_CLOSED
        self.board.save(update_fields=['status', 'updated_at'])

        response = self.client.post(
            reverse('board:create_question', args=[self.board.code]),
            {'nickname': 'Alice', 'text': 'Can I post here?'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Question.objects.filter(board=self.board).count(), 0)

    def test_closed_board_rejects_vote(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Question')
        self.board.status = Board.STATUS_CLOSED
        self.board.save(update_fields=['status', 'updated_at'])

        response = self.client.post(reverse('board:vote_question', args=[self.board.code, question.pk]))

        self.assertEqual(response.status_code, 302)
        question.refresh_from_db()
        self.assertEqual(question.vote_count, 0)
        self.assertEqual(Vote.objects.filter(question=question).count(), 0)

    def test_closed_board_page_shows_closed_notice(self):
        self.board.status = Board.STATUS_CLOSED
        self.board.save(update_fields=['status', 'updated_at'])

        response = self.client.get(reverse('board:home', args=[self.board.code]))
        self.assertContains(response, 'Board closed')


class JoinByCodeTests(BoardScopedTests):
    def test_valid_code_redirects_to_board_home(self):
        response = self.client.post(reverse('board:join_by_code'), {'code': self.board.code})
        self.assertRedirects(response, reverse('board:home', args=[self.board.code]))

    def test_invalid_code_redirects_to_landing(self):
        response = self.client.post(reverse('board:join_by_code'), {'code': 'missing12'})
        self.assertRedirects(response, reverse('board:landing'))

    def test_code_input_is_case_insensitive(self):
        response = self.client.post(reverse('board:join_by_code'), {'code': self.board.code.upper()})
        self.assertRedirects(response, reverse('board:home', args=[self.board.code]))

    def test_empty_code_redirects_to_landing(self):
        response = self.client.post(reverse('board:join_by_code'), {'code': '   '})
        self.assertRedirects(response, reverse('board:landing'))

    def test_get_join_route_redirects_to_landing(self):
        response = self.client.get(reverse('board:join_by_code'))
        self.assertRedirects(response, reverse('board:landing'))


class OwnerBoardQRTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='owner1', password='owner-pass-123')
        self.other_owner = get_user_model().objects.create_user(username='owner2', password='owner-pass-456')
        self.board = Board.objects.create(title='Owner Board', owner=self.owner)
        self.other_board = Board.objects.create(title='Other Board', owner=self.other_owner)

    def test_qr_requires_login(self):
        response = self.client.get(reverse('board:owner_board_qr', args=[self.board.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('board:sign_in'), response['Location'])

    def test_owner_can_fetch_qr_png(self):
        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.get(reverse('board:owner_board_qr', args=[self.board.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_owner_can_download_qr_with_filename(self):
        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.get(reverse('board:owner_board_qr', args=[self.board.id]) + '?download=1')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="board-{self.board.code}.png"')

    def test_non_owner_cannot_access_qr(self):
        self.client.login(username='owner1', password='owner-pass-123')
        response = self.client.get(reverse('board:owner_board_qr', args=[self.other_board.id]))
        self.assertEqual(response.status_code, 404)
