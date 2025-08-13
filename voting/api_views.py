# voting/api_views.py

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.utils import timezone
from django.db.models import Count
from django.db import IntegrityError
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.utils.translation import gettext as _
import csv
from io import BytesIO
from reportlab.pdfgen import canvas
from rest_framework.throttling import ScopedRateThrottle

from .models import (
    Election, Candidate, Vote, VoteAuditLog, Category, Notification
)
from .serializers import (
    ElectionSerializer, CandidateSerializer, VoteSerializer,
    CategorySerializer, NotificationSerializer
)
from .permissions import IsAdminUser, IsElectionCreator, IsVoter, IsAdminOrModerator
from accounts.models import CustomUser


# -------------------- Elections --------------------
class ElectionViewSet(viewsets.ModelViewSet):
    serializer_class = ElectionSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsElectionCreator()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        elif self.action in [
            'deactivate', 'lock', 'unlock',
            'flag', 'unflag', 'mark_reviewed', 'mark_unreviewed'
        ]:
            return [IsAdminOrModerator()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        qs = Election.objects.filter(is_active=True, is_reviewed=True, is_flagged=False)
        if self.request.user.is_staff:
            return Election.objects.all()
        return qs

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        election = self.get_object()
        election.is_active = False
        election.save()
        return Response({'status': 'Election deactivated'})

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        election = self.get_object()
        election.is_locked = True
        election.save()
        return Response({'status': 'Election locked'})

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        election = self.get_object()
        election.is_locked = False
        election.save()
        return Response({'status': 'Election unlocked'})

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        election = self.get_object()
        election.is_flagged = True
        election.save()
        return Response({'status': 'Election flagged for review'})

    @action(detail=True, methods=['post'])
    def unflag(self, request, pk=None):
        election = self.get_object()
        election.is_flagged = False
        election.save()
        return Response({'status': 'Election unflagged'})

    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        election = self.get_object()
        election.is_reviewed = True
        election.save()
        return Response({'status': 'Election marked as reviewed'})

    @action(detail=True, methods=['post'])
    def mark_unreviewed(self, request, pk=None):
        election = self.get_object()
        election.is_reviewed = False
        election.save()
        return Response({'status': 'Election marked as unreviewed'})

    def update(self, request, *args, **kwargs):
        election = self.get_object()
        if election.is_locked:
            return Response({'detail': 'Election is locked and cannot be edited.'}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        election = self.get_object()
        if election.is_locked:
            return Response({'detail': _('Election is locked and cannot be deleted.')}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def export_csv(self, request, pk=None):
        election = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{election.title}_results.csv"'
        writer = csv.writer(response)
        writer.writerow(['Candidate', 'Party', 'Votes'])
        for candidate in election.candidates.all():
            writer.writerow([candidate.name, candidate.party, candidate.votes_count])
        return response

    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def export_pdf(self, request, pk=None):
        election = self.get_object()
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("Helvetica", 14)
        p.drawString(100, 800, f"Election Results: {election.title}")
        y = 760
        p.setFont("Helvetica", 12)
        p.drawString(100, y, "Candidate       |       Party       |       Votes")
        y -= 20
        for candidate in election.candidates.all():
            line = f"{candidate.name}       |       {candidate.party}       |       {candidate.votes_count}"
            p.drawString(100, y, line)
            y -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        election = self.get_object()
        user = request.user

        election.lock_if_ended()

        if not election.show_results_immediately and timezone.now() < election.end_date:
            return Response(
                {'detail': 'Results will be available after the election ends.'},
                status=status.HTTP_403_FORBIDDEN
            )

        candidates = election.candidates.all()
        total_votes = sum(c.votes_count for c in candidates)

        results_data = []
        for c in candidates:
            percentage = (c.votes_count / total_votes * 100) if total_votes > 0 else 0
            results_data.append({
                'candidate_id': c.id,
                'name': c.name,
                'party': c.party,
                'votes': c.votes_count,
                'percentage': round(percentage, 2)
            })

        has_voted = Vote.objects.filter(voter=user, election=election).exists()

        return Response({
            'election': election.title,
            'results': results_data,
            'has_voted': has_voted
        })


# -------------------- Candidates --------------------
class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsElectionCreator()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        elif self.action in ['deactivate', 'flag', 'unflag', 'mark_reviewed', 'mark_unreviewed']:
            return [IsAdminOrModerator()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        election_id = self.request.query_params.get('election')
        qs = Candidate.objects.filter(is_active=True, is_reviewed=True, is_flagged=False)
        if election_id:
            qs = qs.filter(election_id=election_id)
        if self.request.user.is_staff:
            return Candidate.objects.all()
        return qs

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        candidate = self.get_object()
        candidate.is_active = False
        candidate.save()
        return Response({'status': 'Candidate deactivated'})

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        candidate = self.get_object()
        candidate.is_flagged = True
        candidate.save()
        return Response({'status': 'Candidate flagged for review'})

    @action(detail=True, methods=['post'])
    def unflag(self, request, pk=None):
        candidate = self.get_object()
        candidate.is_flagged = False
        candidate.save()
        return Response({'status': 'Candidate unflagged'})

    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        candidate = self.get_object()
        candidate.is_reviewed = True
        candidate.save()
        return Response({'status': 'Candidate marked as reviewed'})

    @action(detail=True, methods=['post'])
    def mark_unreviewed(self, request, pk=None):
        candidate = self.get_object()
        candidate.is_reviewed = False
        candidate.save()
        return Response({'status': 'Candidate marked as unreviewed'})


# -------------------- Votes --------------------
class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'vote'

    def get_permissions(self):
        # Keep your custom IsVoter for create (should allow guests when permitted)
        if self.action == 'create':
            return [IsVoter()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Users see their own votes
        return Vote.objects.filter(voter=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        election_id = request.data.get('election')
        candidate_id = request.data.get('candidate')
        comment = (request.data.get('comment') or '').strip()
        device_fp = (request.data.get('device_fingerprint') or '').strip()

        # Election
        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            return Response({'detail': 'Election does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Voting window
        now = timezone.now()
        if now < election.start_date or now > election.end_date:
            return Response(
                {'detail': 'Voting is not allowed outside the election period.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Candidate sanity: must belong to this election
        try:
            candidate = Candidate.objects.get(id=candidate_id, election=election)
        except Candidate.DoesNotExist:
            return Response({'detail': 'Candidate not found for this election.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Comment requirement
        if election.allow_vote_comments and not comment:
            return Response({'detail': 'A comment is required for this vote.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Duplicate blocking rules
        # 1) Logged-in users: always one vote per election (even if allow_anonymous=True)
        if user and Vote.objects.filter(voter=user, election=election).exists():
            return Response({'detail': 'You have already voted in this election.'},
                            status=status.HTTP_409_CONFLICT)

        # 2) Guests: require fingerprint and dedupe by fingerprint
        if not user:
            if not election.allow_anonymous:
                return Response({'detail': 'Authentication required to vote.'},
                                status=status.HTTP_401_UNAUTHORIZED)
            if not device_fp:
                return Response({'detail': 'Device fingerprint is required for anonymous voting.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if Vote.objects.filter(election=election, device_fingerprint=device_fp).exists():
                return Response({'detail': 'This device has already voted in this election.'},
                                status=status.HTTP_409_CONFLICT)

        # Stash for perform_create
        request._election = election
        request._candidate = candidate
        request._comment = comment
        request._device_fp = device_fp
        request._voter = user  # may be None (guest)

        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # Covers race conditions with unique constraints (voter+election or election+fingerprint)
            return Response({'detail': 'Duplicate vote detected.'}, status=status.HTTP_409_CONFLICT)

    def perform_create(self, serializer):
        election = getattr(self.request, '_election', None)
        candidate = getattr(self.request, '_candidate', None)
        comment = getattr(self.request, '_comment', '')
        device_fp = getattr(self.request, '_device_fp', '')
        voter = getattr(self.request, '_voter', None)

        # Always attribute vote to the user when authenticated; guests get voter=None
        vote = serializer.save(
            voter=voter,
            election=election,
            candidate=candidate,
            comment=comment,
            device_fingerprint=(device_fp or None),
        )

        # Audit log
        VoteAuditLog.objects.create(
            voter=voter,
            election=vote.election,
            candidate=vote.candidate,
            action='create',
            comment_snapshot=vote.comment
        )

        # Push a live update via channels (if configured)
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"election_{election.id}",
                {
                    "type": "vote_update",
                    "data": {
                        "candidate_id": vote.candidate.id,
                        "total_votes": vote.candidate.votes_count
                    }
                }
            )

        # Notify authenticated voters
        if voter:
            Notification.objects.create(
                recipient=voter,
                message=f"Your vote for '{vote.candidate.name}' in '{vote.election.title}' was recorded."
            )
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{voter.id}",
                    {
                        "type": "notification_message",
                        "message": f"Your vote for '{vote.candidate.name}' in '{vote.election.title}' was recorded.",
                        "link": f"/elections/{vote.election.id}/results/"
                    }
                )


# -------------------- Categories --------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


# -------------------- Notifications --------------------
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'Notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({'status': 'All notifications marked as read'})


# -------------------- Admin Stats --------------------
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    total_users = CustomUser.objects.count()
    users_by_role = CustomUser.objects.values('role').annotate(count=Count('id'))

    total_elections = Election.objects.count()
    active_elections = Election.objects.filter(is_active=True).count()
    inactive_elections = total_elections - active_elections

    total_candidates = Candidate.objects.count()
    total_votes = Vote.objects.count()
    total_categories = Category.objects.count()

    top_elections = Election.objects.annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count')[:5]

    top_elections_data = [{
        'id': e.id,
        'title': e.title,
        'vote_count': e.vote_count
    } for e in top_elections]

    return Response({
        'users': {
            'total': total_users,
            'by_role': users_by_role
        },
        'elections': {
            'total': total_elections,
            'active': active_elections,
            'inactive': inactive_elections,
            'top_by_votes': top_elections_data
        },
        'candidates': total_candidates,
        'votes': total_votes,
        'categories': total_categories,
    })
