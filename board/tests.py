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
        self.staff = get_user_model().objects.create_user(
            username='host', password='hostpass', is_staff=True
        )

    def test_manage_redirects_unauthenticated_to_login(self):
        response = self.client.get(reverse('board:manage'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_staff_can_hide_active_question(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test')
        self.client.force_login(self.staff)
        self.client.post(
            reverse('board:moderate_question', args=[question.pk]),
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
        self.client.force_login(self.staff)
        self.client.post(
            reverse('board:moderate_question', args=[question.pk]),
            {'state': 'hidden'}
        )
        question.refresh_from_db()
        self.assertEqual(question.state, Question.STATE_ARCHIVED)

    def test_staff_can_restore_archived_to_active(self):
        question = Question.objects.create(board=self.board, nickname='Alice', text='Test', state=Question.STATE_ARCHIVED)
        self.client.force_login(self.staff)
        self.client.post(
            reverse('board:moderate_question', args=[question.pk]),
            {'state': 'active'}
        )
        question.refresh_from_db()
        self.assertEqual(question.state, Question.STATE_ACTIVE)


class HTMXVoteTests(BoardScopedTests):
    def test_standard_get_returns_full_page_template(self):
        response = self.client.get(reverse('board:home', args=[self.board.code]))
        self.assertTemplateUsed(response, 'board/home.html')
        self.assertTemplateNotUsed(response, 'board/partials/question_list.html')

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
