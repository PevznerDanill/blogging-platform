from django.views.generic import TemplateView
from app_auth.models import Profile
from app_rss.feeds import LatestPostsFeed
from app_auth.utils import get_profile_for_context
from typing import Dict, Union
from django.db.models import QuerySet
from django.views import View


class IndexView(TemplateView):
    """
    A view to display the main page.
    """
    template_name = 'app_main/index.html'

    def get_context_data(self, **kwargs) -> Dict[str, Union[View, Profile, QuerySet]]:
        """
        Adds Profile instance related to the authenticated user and feeds to the context.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile = get_profile_for_context(self.request)
            context['profile'] = profile
        latest_posts_feed = LatestPostsFeed()
        latest_posts = latest_posts_feed.get_context_data()
        context.update(latest_posts)
        return context


class AboutView(TemplateView):
    """
    A view to render the app_main/about.html
    """
    template_name = 'app_main/about.html'

    def get_context_data(self, **kwargs) -> Dict[str, Union[View, Profile]]:
        """
        Adds Profile instance related to the authenticated user and feeds to the context.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile = get_profile_for_context(self.request)
            context['profile'] = profile
        return context


class ContactView(TemplateView):
    """
    A view to render the app_main/contact.html
    """
    template_name = 'app_main/contact.html'

    def get_context_data(self, **kwargs) -> Dict[str, Union[View, Profile]]:
        """
        Adds Profile instance related to the authenticated user and feeds to the context.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile = get_profile_for_context(self.request)
            context['profile'] = profile
        return context
