# voting/serializers.py

from rest_framework import serializers
from .models import Election, Candidate, Vote, Category, Notification

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


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


class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Election
        fields = [
            'id', 'title', 'description', 'category',
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


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'voter', 'candidate', 'election', 'timestamp', 'comment']
        read_only_fields = ['voter', 'timestamp']


# --- Notifications ---
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
