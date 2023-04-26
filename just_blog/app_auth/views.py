from django.shortcuts import render, reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.contrib.auth import authenticate, login


class GetStartedView(CreateView):
    form_class = UserCreationForm
    template_name = 'app_auth/get-started.html'

    def form_valid(self, form):
        self.object = form.save()
        self.profile = Profile(user=self.request.user)
        self.profile.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(
            request=self.request,
            username=username,
            password=password
        )
        login(
            request=self.request,
            user=user
        )
        result = HttpResponseRedirect(self.get_success_url())
        return result

    def get_success_url(self):
        pk = self.profile.pk
        return reverse('app_auth:profile_edit', kwargs={'pk': pk})





