from django.shortcuts import render, reverse, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import MyUserChangeForm, ProfileForm
from django.urls import reverse_lazy


class GetStartedView(CreateView):
    form_class = UserCreationForm
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
            return HttpResponse(content='You can not update the profile of other user', status=404)

    user_form = MyUserChangeForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(request.POST, request.FILES or None, instance=request.user.profile)

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('app_auth:profile', pk=pk)

    context = {
        'form': user_form,
        'form_1': profile_form,
    }

    return render(request, 'app_auth/profile_update.html', context=context)


class MyLoginView(LoginView):
    template_name = 'app_auth/login.html'

    def get_success_url(self):
        return reverse('app_auth:profile')


class MyLogoutView(LogoutView):
    next_page = reverse_lazy('app_main:index')


