from django.http import Http404
from django.shortcuts import render, get_object_or_404, reverse
from django.views.generic import TemplateView
from app_auth.models import Profile
from app_rss.feeds import LatestPostsFeed


class IndexView(TemplateView):
    template_name = 'app_main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile = get_object_or_404(Profile, user=self.request.user)
            context['profile'] = profile
        latest_posts_feed = LatestPostsFeed()
        latest_posts = latest_posts_feed.get_context_data()
        context.update(latest_posts)
        return context


