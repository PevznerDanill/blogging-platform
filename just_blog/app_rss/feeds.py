from django.contrib.syndication.views import Feed
from django.db.models import QuerySet
from django.shortcuts import reverse
from app_blog.models import Post
from django.db.models import F
import re


class LatestPostsFeed(Feed):
    """
    A feed that shows the last five published posts.
    """
    title = 'Posts'
    link = '/siteposts/'
    description = 'The latest published posts'

    def items(self) -> QuerySet:
        """
        Retrieves five latest published Post instances.
        """
        return Post.objects.select_related('profile').annotate(profile_username=F('profile__user__username')).filter(is_published=True).order_by('-published_at')[:5]

    def item_title(self, item: Post) -> str:
        return re.sub(r'\.\B', '', item.title)

    def item_description(self, item: Post) -> str:
        return item.short_content()

    def item_link(self, item: Post) -> str:
        return reverse('app_blog:post_detail', kwargs={'pk': item.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_posts'] = self.items()
        return context
