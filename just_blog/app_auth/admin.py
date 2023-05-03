from django.contrib import admin
from .models import Profile
from app_blog.models import Blog, Post


class BlogInline(admin.TabularInline):

    model = Blog


class PostInline(admin.StackedInline):
    model = Post


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = 'pk', 'user',
    inlines = [BlogInline, PostInline]




