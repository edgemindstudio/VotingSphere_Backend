# voting/admin.py

from django.contrib import admin
from .models import Election, Candidate, Vote, Category, VoteAuditLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'show_results_immediately', 'creator', 'created_at']
    search_fields = ['title']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'party', 'election', 'votes_count']
    search_fields = ['name', 'party']
    list_filter = ['election']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter_display', 'candidate', 'election']
    list_filter = ['election']

    def voter_display(self, obj):
        return obj.voter.username if obj.voter else "Anonymous"

    voter_display.short_description = 'Voter'


@admin.register(VoteAuditLog)
class VoteAuditLogAdmin(admin.ModelAdmin):
    list_display = ['voter', 'election', 'candidate', 'action', 'timestamp']
    list_filter = ['action', 'election']
    search_fields = ['voter__username', 'candidate__name']