from django.contrib.sitemaps import Sitemap
from .models import Post
from django.db.models import QuerySet


class PostSiteMap(Sitemap):
    """
    Sitemap object for published Posts.
    """
    def items(self) -> QuerySet:
        return Post.objects.filter(is_published=True)

    def lastmod(self, obj: Post):
        print(type(obj.published_at))
        return obj.published_at
