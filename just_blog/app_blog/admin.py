from django.contrib import admin
from .models import Blog, Post, Image


class PostInline(admin.TabularInline):
    model = Post


class ImageInline(admin.StackedInline):
    model = Image


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = 'pk', 'title', 'profile',
    inlines = [PostInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = 'pk', 'title', 'profile',
    inlines = [ImageInline]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = 'pk', 'title', 'post',
