from django.contrib.syndication.views import Feed
from django.db.models import QuerySet
from django.shortcuts import reverse
from app_blog.models import Post


class LatestPostsFeed(Feed):
    title = 'Posts'
    link = '/siteposts/'
    description = 'The latest published posts'

    def items(self) -> QuerySet:
        return Post.objects.select_related('profile').filter(is_published=True).order_by('-published_at')[:5]

    def item_title(self, item: Post) -> str:
        return item.title

    def item_description(self, item: Post) -> str:
        return item.title

    def item_link(self, item: Post) -> str:
        return reverse('app_blog:post_detail', kwargs={'pk': item.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_posts'] = self.items()
        return context
