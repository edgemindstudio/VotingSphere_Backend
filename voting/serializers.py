# voting/serializers.py

from rest_framework import serializers
from .models import Election, Candidate, Vote, Category, Notification


# ---------- Categories ----------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


# ---------- Candidates ----------
class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'bio', 'party', 'votes_count', 'election', 'is_active',
            'is_flagged', 'is_reviewed'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or not request.user.is_staff:
            data.pop('is_flagged', None)
            data.pop('is_reviewed', None)
        return data


# ---------- Elections ----------
class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    # CHANGED: accept category by primary key (id) for writes
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )
    # Optional convenience: include the category name in responses
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Election
        fields = [
            'id', 'title', 'description',
            'category', 'category_name',
            'start_date', 'end_date', 'show_results_immediately',
            'allow_anonymous', 'allow_vote_comments',
            'creator', 'created_at', 'candidates', 'is_flagged', 'is_reviewed'
        ]
        read_only_fields = ['creator']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or not request.user.is_staff:
            data.pop('is_flagged', None)
            data.pop('is_reviewed', None)
        return data


# ---------- Votes ----------
class VoteSerializer(serializers.ModelSerializer):
    # Accept the fingerprint the frontend sends (used to dedupe guests)
    device_fingerprint = serializers.CharField(
        max_length=64, allow_blank=True, required=False
    )

    class Meta:
        model = Vote
        fields = [
            'id',
            'voter',
            'candidate',
            'election',
            'timestamp',
            'comment',
            'device_fingerprint',
        ]
        read_only_fields = ['voter', 'timestamp']

    def validate(self, attrs):
        """
        Guardrails:
        - candidate must belong to election
        """
        election = attrs.get('election')
        candidate = attrs.get('candidate')
        if election and candidate and candidate.election_id != election.id:
            raise serializers.ValidationError(
                {'candidate': 'Selected candidate does not belong to this election.'}
            )
        return attrs


# ---------- Notifications ----------
class NotificationSerializer(serializers.ModelSerializer):
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)
    recipient_username = serializers.CharField(source="recipient.username", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "type", "message", "link",
            "read", "created_at",
            "recipient", "recipient_username",
        ]
        read_only_fields = ["id", "created_at", "recipient", "recipient_username"]
