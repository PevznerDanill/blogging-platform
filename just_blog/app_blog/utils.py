from .models import Blog, Post


def save_post_from_csv(csv_reader, profile, kwargs):
    for row in csv_reader:
        title = row[0]
        tag = row[1]
        content = row[2]
        if not len(title) <= 70 and not len(row) == 3:
            return False
        blog_pk = kwargs.get('pk')
        blog_instance = Blog.objects.get(pk=blog_pk)
        profile_instance = profile
        new_post = Post(content=content, blog=blog_instance, title=title, tag=tag, profile=profile_instance)
        new_post.save()

        return True
