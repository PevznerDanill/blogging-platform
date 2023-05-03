from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView
from .models import Profile
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import MyUserChangeForm, ProfileForm, MyLoginForm, MyUserCreationForm
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from .utils import get_profile_for_context


class GetStartedView(CreateView):
    form_class = MyUserCreationForm
    template_name = 'app_auth/get-started.html'

    def form_valid(self, form):
        self.object = form.save()
        self.profile = Profile(user=self.object)
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
        return reverse('app_auth:profile_update', kwargs={'pk': pk})


@login_required
def update_view(request: HttpRequest, pk):
    if request.user.profile.pk != pk:
        if not request.user.is_superuser:
            raise PermissionDenied
    if request.method == 'POST':
        user_form = MyUserChangeForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('app_auth:profile_detail', pk=pk)

    else:
        user_form = MyUserChangeForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    context = {
        'form': user_form,
        'form_1': profile_form,
        'profile': get_profile_for_context(request)
    }

    return render(request, 'app_auth/profile_update.html', context=context)


class MyLoginView(LoginView):
    template_name = 'app_auth/login.html'
    form_class = MyLoginForm

    def get_success_url(self):
        cur_profile = get_profile_for_context(self.request)
        return reverse('app_auth:profile_detail', kwargs={'pk': cur_profile.pk})


class MyLogoutView(LogoutView):
    next_page = reverse_lazy('app_main:index')


class ProfileDetailView(UserPassesTestMixin, DetailView):
    queryset = (
        Profile.objects.select_related('user')
    )
    template_name = 'app_auth/profile_detail.html'

    context_object_name = 'profile'

    def test_func(self):
        if self.request.user.is_authenticated:
            pk = self.kwargs.get('pk')
            cur_profile = get_profile_for_context(self.request)
            return pk == cur_profile.pk


class ProfilePublicView(DetailView):
    queryset = (
        Profile.objects.select_related('user')
    )
    template_name = 'app_auth/profile_public_detail.html'

    context_object_name = 'cur_profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = get_profile_for_context(self.request)

        return context
