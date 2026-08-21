from django.test import TestCase
from django.urls import reverse

from .models import Question, Vote


class QuestionBoardTests(TestCase):
    def test_create_question_and_list_it(self):
        response = self.client.post(
            reverse('board:create_question'),
            {'nickname': 'Alice', 'text': 'Can we add question sorting?'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Question.objects.get().nickname, 'Alice')

    def test_questions_are_ordered_by_votes_then_newest(self):
        first = Question.objects.create(nickname='one', text='First', vote_count=1)
        second = Question.objects.create(nickname='two', text='Second', vote_count=3)
        third = Question.objects.create(nickname='three', text='Third', vote_count=3)

        qs = list(Question.objects.order_by('-vote_count', '-created_at', '-id'))
        self.assertEqual(qs[0].id, third.id)
        self.assertEqual(qs[1].id, second.id)
        self.assertEqual(qs[2].id, first.id)

    def test_same_browser_can_only_vote_once_per_question(self):
        question = Question.objects.create(nickname='Host', text='Test question')
        response = self.client.post(
            reverse('board:vote_question', args=[question.pk]),
            HTTP_COOKIE='board_voter=abc123'
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(question.votes.count(), 1)

        second_response = self.client.post(
            reverse('board:vote_question', args=[question.pk]),
            HTTP_COOKIE='board_voter=abc123'
        )

        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(question.votes.count(), 1)
