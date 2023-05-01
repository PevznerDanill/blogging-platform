from django.contrib import admin
from .models import Blog, Post, Image


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = 'pk', 'title', 'profile',


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = 'pk', 'title', 'profile',
