# voting/models.py

from django.db import models
from django.conf import settings  # uses settings.AUTH_USER_MODEL
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q  # NEW: for conditional unique constraints


class Election(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='elections'
    )
    allow_anonymous = models.BooleanField(
        default=False,
        help_text="If true, votes can be submitted without a user."
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    show_results_immediately = models.BooleanField(
        default=False,
        help_text="If true, results are visible immediately after voting; otherwise, only after the election ends."
    )
    allow_vote_comments = models.BooleanField(
        default=False,
        help_text="If true, users can (or must) add a comment when voting."
    )
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='elections_created')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False, help_text="Locked after end date to prevent editing.")
    is_flagged = models.BooleanField(default=False, help_text="Flagged for admin review.")
    is_reviewed = models.BooleanField(default=True, help_text="Reviewed and approved by an admin.")

    def lock_if_ended(self):
        if timezone.now() > self.end_date and not self.is_locked:
            self.is_locked = True
            self.save()

    def __str__(self):
        return self.title


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    party = models.CharField(max_length=255, blank=True)
    votes_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False, help_text="Flagged for admin review.")
    is_reviewed = models.BooleanField(default=True, help_text="Reviewed and approved by an admin.")

    def __str__(self):
        return f"{self.name} ({self.party})"


class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # NEW: used to dedupe anonymous voters (and we can store it for authed voters too)
    device_fingerprint = models.CharField(
        max_length=64, null=True, blank=True, db_index=True,
        help_text="Opaque client identifier used to prevent duplicate anonymous votes."
    )

    class Meta:
        constraints = [
            # One vote per logged-in user per election
            models.UniqueConstraint(
                fields=['election', 'voter'],
                name='uniq_vote_per_user',
                condition=Q(voter__isnull=False),
            ),
            # One vote per device per election (for guests / when fingerprint present)
            models.UniqueConstraint(
                fields=['election', 'device_fingerprint'],
                name='uniq_vote_per_device',
                condition=Q(device_fingerprint__isnull=False),
            ),
        ]

    def __str__(self):
        voter_name = getattr(self.voter, 'username', None) or "Anonymous"
        return f"{voter_name} → {self.candidate.name}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class VoteAuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('delete', 'Delete'),
    ]

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment_snapshot = models.TextField(blank=True, null=True)

    def __str__(self):
        voter_name = getattr(self.voter, 'username', None) or "Anonymous"
        return f"[{self.timestamp}] {self.action.upper()} by {voter_name} for {self.candidate.name}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('vote_confirmation', 'Vote Confirmation'),
        ('election_update', 'Election Update'),
        ('results_published', 'Results Published'),
        ('admin_message', 'Admin Message'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='vote_confirmation')
    link = models.URLField(blank=True, null=True, help_text="Optional link to related content")
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"To: {self.recipient} | {self.type} | {self.message[:40]}"
