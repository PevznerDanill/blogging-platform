from django.contrib import admin
from .models import Profile
from app_blog.models import Blog, Post

"""
Register in the admin panel the model Profile, with related Blog and Post models as inlines.
"""


class BlogInline(admin.TabularInline):
    model = Blog


class PostInline(admin.StackedInline):
    model = Post


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = 'pk', 'user',
    inlines = [BlogInline, PostInline]




