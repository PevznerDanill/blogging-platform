from .models import Blog, Post
from csv import reader
from app_auth.models import Profile
from typing import Optional


def save_post_from_csv(csv_reader: reader, profile: Profile, kwargs) -> Optional[Post]:
    """
    Takes title, tag and content from every row of the reader and creates a new Post instance.
    """
    for row in csv_reader:
        title = row[0]
        tag = row[1]
        content = row[2]
        if not len(title) <= 70 and not len(row) == 3:
            return None
        blog_pk = kwargs.get('pk')
        blog_instance: Blog = Blog.objects.get(pk=blog_pk)
        profile_instance = profile
        new_post = Post(content=content, blog=blog_instance, title=title, tag=tag, profile=profile_instance)
        new_post.save()

        return new_post
