from django.db import models


class Question(models.Model):
    STATE_ACTIVE = 'active'
    STATE_HIDDEN = 'hidden'
    STATE_ARCHIVED = 'archived'
    STATE_CHOICES = [
        (STATE_ACTIVE, 'Active'),
        (STATE_HIDDEN, 'Hidden'),
        (STATE_ARCHIVED, 'Archived'),
    ]

    nickname = models.CharField(max_length=50)
    text = models.TextField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_ACTIVE)
    vote_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-vote_count', '-created_at', '-id']

    def __str__(self):
        return f'{self.nickname}: {self.text[:40]}'


class Vote(models.Model):
    question = models.ForeignKey(Question, related_name='votes', on_delete=models.CASCADE)
    voter_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['question', 'voter_token'], name='unique_vote_per_question_per_voter')
        ]

    def __str__(self):
        return f'{self.question_id}:{self.voter_token}'
