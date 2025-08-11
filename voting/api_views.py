# voting/api_views.py

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Election, Candidate, Vote, VoteAuditLog, Category, Notification
from .serializers import ElectionSerializer, CandidateSerializer, VoteSerializer, CategorySerializer, NotificationSerializer
from django.db.models import Q
from datetime import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .permissions import IsAdminUser, IsElectionCreator, IsVoter, IsAdminOrModerator
from rest_framework.decorators import api_view, permission_classes
from accounts.models import CustomUser  # Assuming CustomUser is in accounts.models
from django.db.models import Count
import csv
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO
from rest_framework.throttling import ScopedRateThrottle
from django.utils.translation import gettext as _



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
            return Response({'detail': 'Results will be available after the election ends.'},
                            status=status.HTTP_403_FORBIDDEN)

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


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsElectionCreator()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        elif self.action in [
            'deactivate', 'flag', 'unflag', 'mark_reviewed', 'mark_unreviewed'
        ]:
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


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'vote'

    def get_permissions(self):
        if self.action == 'create':
            return [IsVoter()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Vote.objects.filter(voter=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        election_id = request.data.get('election')
        comment = request.data.get('comment', '')

        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            return Response({'detail': 'Election does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        if now < election.start_date or now > election.end_date:
            return Response({'detail': 'Voting is not allowed outside the election period.'},
                            status=status.HTTP_403_FORBIDDEN)

        if not election.allow_anonymous:
            if not request.user.is_authenticated:
                return Response({'detail': 'Authentication required to vote.'}, status=status.HTTP_401_UNAUTHORIZED)

            if Vote.objects.filter(voter=request.user, election=election).exists():
                return Response({'detail': 'You have already voted in this election.'},
                                status=status.HTTP_400_BAD_REQUEST)

        if election.allow_vote_comments and not comment:
            return Response({'detail': 'A comment is required for this vote.'},
                            status=status.HTTP_400_BAD_REQUEST)

        request._election = election
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        election = getattr(self.request, '_election', None)
        comment = self.request.data.get('comment', '')
        voter = None if election and election.allow_anonymous else self.request.user
        vote = serializer.save(voter=voter, comment=comment)

        # Create audit log
        VoteAuditLog.objects.create(
            voter=voter,
            election=vote.election,
            candidate=vote.candidate,
            action='create',
            comment_snapshot=vote.comment
        )

        # Setup WebSocket layer
        channel_layer = get_channel_layer()

        # Send live vote update to election group
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

        # Create notification and push it via WebSocket
        if voter:
            Notification.objects.create(
                recipient=voter,
                message=f"Your vote for '{vote.candidate.name}' in '{vote.election.title}' was recorded."
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{voter.id}",
                {
                    "type": "notification_message",
                    "message": f"Your vote for '{vote.candidate.name}' in '{vote.election.title}' was recorded.",
                    "link": f"/elections/{vote.election.id}/results/"
                }
            )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


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