import secrets
import string

from django.conf import settings
from django.db import models
from django.urls import reverse


def _generate_board_code(length=8):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Board(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=100)
    code = models.CharField(max_length=16, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='owned_boards',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', '-created_at', '-id'], name='board_status_created_idx'),
            models.Index(fields=['owner', '-created_at', '-id'], name='board_owner_created_idx'),
        ]

    def __str__(self):
        return self.title

    def get_public_url(self, request):
        return request.build_absolute_uri(reverse('board:home', args=[self.code]))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_unique_code(cls):
        while True:
            code = _generate_board_code()
            if not cls.objects.filter(code=code).exists():
                return code


class Question(models.Model):
    STATE_ACTIVE = 'active'
    STATE_HIDDEN = 'hidden'
    STATE_ARCHIVED = 'archived'
    STATE_CHOICES = [
        (STATE_ACTIVE, 'Active'),
        (STATE_HIDDEN, 'Hidden'),
        (STATE_ARCHIVED, 'Archived'),
    ]

    board = models.ForeignKey(Board, related_name='questions', on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50)
    text = models.TextField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_ACTIVE)
    vote_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-vote_count', '-created_at', '-id']
        indexes = [
            models.Index(
                fields=['board', 'state', '-vote_count', '-created_at', '-id'],
                name='question_board_rank_idx',
            ),
        ]

    _ALLOWED_TRANSITIONS = {
        'active':   {'hidden', 'archived'},
        'hidden':   {'active', 'archived'},
        'archived': {'active'},
    }

    def __str__(self):
        return f'{self.board_id}:{self.nickname}: {self.text[:40]}'

    def transition_to(self, new_state):
        allowed = self._ALLOWED_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(f"Cannot transition from '{self.state}' to '{new_state}'")
        self.state = new_state
        self.save(update_fields=['state', 'updated_at'])


class Vote(models.Model):
    question = models.ForeignKey(Question, related_name='votes', on_delete=models.CASCADE)
    voter_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['question', 'voter_token'], name='unique_vote_per_question_per_voter')
        ]
        indexes = [
            models.Index(fields=['voter_token', 'question'], name='vote_token_question_idx'),
        ]

    def __str__(self):
        return f'{self.question_id}:{self.voter_token}'
