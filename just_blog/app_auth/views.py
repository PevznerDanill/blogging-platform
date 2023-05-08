from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.views.generic import CreateView, DetailView
from .models import Profile
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import MyUserChangeForm, ProfileForm, MyLoginForm, MyUserCreationForm
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from .utils import get_profile_for_context
from typing import Union, Dict


class GetStartedView(CreateView):
    """
    A view to initiate the registration process.
    """
    form_class = MyUserCreationForm
    template_name = 'app_auth/get-started.html'

    def form_valid(self, form: MyUserCreationForm) -> HttpResponseRedirect:
        """
        Overrides the default form_valid method, adding to it the creation of a new
        related Profile instance and performing the login of the new user.
        Also declares this new profile instance and the self.object with the user instance.
        """
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

    def get_success_url(self) -> str:
        """
        Gets the pk of the saved Profile instance to generate
        an url to the app_auth:profile_update path.
        """
        pk = self.profile.pk
        return reverse('app_auth:profile_update', kwargs={'pk': pk})


@login_required
def update_view(request: HttpRequest, pk: int) -> Union[HttpResponseRedirect, HttpResponse, PermissionDenied]:
    """
    A view that processes an update of the Profile instance.

    First, it checks if the passed pk of the Profile instance is the same as the pk
    of the Profile instance related to the current User instance saved in request.user.
    If not, raises PermissionDenied error. If the user isn't authenticated, redirects to the Login form.

    Then, it works with two forms: MyUserChangeForm, that allows to fill the fields first_name,
    last_name and email of the User model;
    and ProfileForm with the fields bio, age and avatar.
    If both forms a valid, saves the changes and redirects to the app_auth:profile_detail path.
    """
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
    """
    A view for login.
    """
    template_name = 'app_auth/login.html'
    form_class = MyLoginForm

    def get_success_url(self) -> str:
        """
        Gets the Profile instance related to request.user instance and
        takes its pk to generate a link to the app_auth:profile_detail path.
        """
        cur_profile = get_profile_for_context(self.request)
        return reverse('app_auth:profile_detail', kwargs={'pk': cur_profile.pk})


class MyLogoutView(LogoutView):
    """
    Overrides the default LogoutView, setting the next_page argument to a lazy reverse to the main page.
    """
    next_page = reverse_lazy('app_main:index')


class ProfileDetailView(UserPassesTestMixin, DetailView):
    """
    A view for the details of Profile instance.
    """
    queryset = (
        Profile.objects.select_related('user')
    )
    template_name = 'app_auth/profile_detail.html'

    context_object_name = 'profile'

    def test_func(self) -> bool:
        """
        Checks if the user is authenticated and if his Profile instance's pk os the same as the
        pk passed in the kwargs.
        If the user isn't authenticated, redirects to the Login form.
        """
        if self.request.user.is_authenticated:
            pk = self.kwargs.get('pk')
            cur_profile = get_profile_for_context(self.request)
            return pk == cur_profile.pk


class ProfilePublicView(DetailView):
    """
    The same view as the ProfileDetailView, but available for any user.
    """
    queryset = (
        Profile.objects.select_related('user')
    )
    template_name = 'app_auth/profile_public_detail.html'

    context_object_name = 'cur_profile'

    def get_context_data(self, **kwargs) -> Dict[str, Union[Profile, View]]:
        """
        If current user is authenticated, adds its related Profile instance to the context.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = get_profile_for_context(self.request)
        return context
