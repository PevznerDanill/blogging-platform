from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from app_auth.models import Profile


class IndexView(TemplateView):
    template_name = 'app_main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile = get_object_or_404(Profile, user=self.request.user)
            context['profile'] = profile
        return context


