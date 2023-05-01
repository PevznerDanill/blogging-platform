from django.core.exceptions import PermissionDenied
from django.shortcuts import render, reverse, redirect, get_object_or_404, get_list_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import Blog, Post, Image
from app_auth.models import Profile
from .forms import BlogForm, PostForm, PostFileForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from csv import reader
from django.http import HttpRequest, HttpResponseRedirect, Http404
from django.db.models import Prefetch, F


class UserBlogListView(ListView):
    template_name = 'app_blog/user_blog_list.html'
    context_object_name = 'blogs'

    def get_queryset(self):
        profile_pk = self.kwargs.get('pk')
        try:
            blogs = get_list_or_404(Blog.objects.select_related('profile').prefetch_related('posts'),
                                    profile__pk=profile_pk)
        except Http404 as exc:
            blogs = None
        return blogs

    def get_context_data(self, *, object_list=None, **kwargs):
        pk = self.kwargs.get('pk')
        context = super().get_context_data(object_list=None, **kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = get_object_or_404(Profile.objects.select_related('user'), user=self.request.user)
        context['cur_profile'] = get_object_or_404(Profile.objects.select_related('user'), pk=pk)
        return context


class BlogCreateView(LoginRequiredMixin, CreateView):
    form_class = BlogForm
    template_name = 'app_blog/blog_new.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.get(user=self.request.user)
        return context

    def form_valid(self, form):
        form.instance.profile = Profile.objects.get(user=self.request.user)
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('app_blog:blog_detail', kwargs={'pk': self.object.pk})


class BlogDetailView(DetailView):
    queryset = (
        Blog.objects.select_related('profile').prefetch_related('posts')
    )
    template_name = 'app_blog/blog_detail.html'
    context_object_name = 'blog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class BlogDeleteView(DeleteView):
    model = Blog
    template_name = 'app_blog/blog_delete.html'
    context_object_name = 'blog'

    def get_success_url(self):
        cur_profile = Profile.objects.get(user=self.request.user)
        return reverse('app_blog:user_blog_list', kwargs={'pk': cur_profile.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class PostDeleteView(DeleteView):
    model = Post
    template_name = 'app_blog/post_delete.html'
    context_object_name = 'post'

    def get_success_url(self):
        return reverse('app_blog:blog_detail', kwargs={'pk': self.blog_pk})

    def form_valid(self, form):
        self.blog_pk = self.object.blog.pk
        result = super().form_valid(form)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class PostCreateView(UserPassesTestMixin, CreateView):

    form_class = PostForm
    template_name = 'app_blog/post_new.html'
    queryset = (
        Post.objects.select_related('blog').prefetch_related('images')
    )

    def test_func(self):
        if self.request.user.is_authenticated:
            pk = self.kwargs.get('pk')
            cur_blog = get_object_or_404(Blog.objects.select_related('profile'), pk=pk)
            cur_user = get_object_or_404(Profile, user=self.request.user)
            return cur_blog.profile.pk == cur_user.pk

    def get_success_url(self, new_object=None):
        if new_object:
            pk = new_object.pk
        else:
            pk = self.object.pk
        return reverse('app_blog:post_detail', kwargs={'pk': pk})

    def form_valid(self, form):
        blog_pk = self.kwargs.get('pk')
        form.instance.blog = Blog.objects.get(pk=blog_pk)
        form.instance.profile = Profile.objects.get(user=self.request.user)
        self.object = form.save()
        if self.request.FILES:
            images = self.request.FILES.getlist('images')
            for img in images:
                image_instance = Image(title=img.name, image=img, post=self.object)
                image_instance.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.get(user=self.request.user)
        context['form'] = self.get_form()
        context['form_1'] = PostFileForm
        return context

    def get_invalid_context(self):
        context = {
            'form': self.get_form(),
            'form_1': PostFileForm,
            'error': 'The file you have just try to upload is invalid'
        }
        return render(self.request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_2 = PostFileForm(request.POST, request.FILES)

        if form.is_valid():
            return self.form_valid(form)

        elif form_2.is_valid():
            csv_file = form_2.cleaned_data['file'].read()
            csv_file_str = csv_file.decode('utf-8').splitlines()
            try:
                csv_reader = reader(csv_file_str, delimiter=',', quotechar='"')
                for row in csv_reader:
                    title = row[0]
                    tag = row[1]
                    content = row[2]
                    if not len(title) <= 70 and not len(row) == 3:
                        return self.get_invalid_context()
                    blog_pk = self.kwargs.get('pk')
                    blog_instance = Blog.objects.get(pk=blog_pk)
                    profile_instance = Profile.objects.get(user=self.request.user)
                    new_post = Post(content=content, blog=blog_instance, title=title, tag=tag, profile=profile_instance)
                    new_post.save()
            except IndexError:
                csv_reader = reader(csv_file_str, delimiter=',', quotechar='"')
                for row in csv_reader:
                    title = row[0]
                    tag = row[1]
                    content = row[2]
                    if not len(title) <= 70 and not len(row) == 3:
                        return self.get_invalid_context()
                    blog_pk = self.kwargs.get('pk')
                    blog_instance = Blog.objects.get(pk=blog_pk)
                    profile_instance = Profile.objects.get(user=self.request.user)
                    new_post = Post(content=content, blog=blog_instance, title=title, tag=tag, profile=profile_instance)
                    new_post.save()
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


# class BlogPostsListView(ListView):
#     template_name = 'app_blog/blog_posts.html'
#     context_object_name = 'posts'
#
#     def get_queryset(self):
#         blog_pk = self.kwargs.get('pk')
#         return Post.objects.select_related('blog').prefetch_related('images').filter(blog__id=blog_pk)
#
#     def get_context_data(self, *, object_list=None, **kwargs):
#         context = super().get_context_data(object_list=None, **kwargs)
#
#         if self.request.user.is_authenticated:
#             context['profile'] = Profile.objects.get(user=self.request.user)
#
#         return context


class PostDetailView(UserPassesTestMixin, DetailView):
    queryset = (
        Post.objects.select_related('blog').prefetch_related('images')
    )
    template_name = 'app_blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = Profile.objects.get(user=self.request.user)
        return context

    def test_func(self):
        cur_profile = None
        if self.request.user.is_authenticated:
            cur_profile = Profile.objects.get(user=self.request.user)
        cur_post = Post.objects.get(pk=self.kwargs.get('pk'))
        return cur_post.is_published or cur_profile == cur_post.profile


class BlogEditView(UserPassesTestMixin, UpdateView):
    form_class = BlogForm
    queryset = (
        Blog.objects.select_related('profile')
    )
    template_name = 'app_blog/blog_edit.html'
    context_object_name = 'blog'

    def test_func(self):
        if self.request.user.is_authenticated:
            cur_blog = get_object_or_404(Blog.objects.select_related('profile'), pk=self.kwargs.get('pk'))
            cur_profile = get_object_or_404(Profile, user=self.request.user)
            return cur_blog.profile == cur_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = Profile.objects.get(user=self.request.user)
        return context

    def get_success_url(self):
        return reverse('app_blog:blog_detail', kwargs={'pk': self.object.pk})


class PostEditView(UserPassesTestMixin, UpdateView):
    queryset = (
        Post.objects.select_related('blog').prefetch_related('images')
    )
    template_name = 'app_blog/post_edit.html'
    form_class = PostForm

    def test_func(self):
        if self.request.user.is_authenticated:
            return (
                get_object_or_404(Post.objects.select_related('profile')).profile ==
                Profile.objects.get(user=self.request.user) or
                self.request.user.is_superuser
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['profile'] = Profile.objects.get(user=self.request.user)
        context['images'] = Image.objects.filter(post=self.object)
        return context

    def get_success_url(self):
        return reverse('app_blog:post_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        self.object = form.save()
        current_images = Image.objects.filter(post=self.object)
        for current_image in current_images:
            if self.request.POST.get(current_image.title) == 'on':
                current_image.delete()
        if self.request.FILES:
            images = self.request.FILES.getlist('images')
            for img in images:
                self.object.images.create(title=img.name, image=img)
        return super().form_valid(form)


@login_required
def publish_or_archive(request: HttpRequest, pk) -> HttpResponseRedirect:
    cur_post = get_object_or_404(Post.objects.select_related('profile'), pk=pk)
    if cur_post.profile != get_object_or_404(Profile, user=request.user):
        raise PermissionDenied
    if cur_post.is_published:
        cur_post.archive()
    else:
        cur_post.publish()
    return redirect(reverse('app_blog:post_detail', kwargs={'pk': pk}))


class LatestPostsView(ListView):
    queryset = (
        Post.objects.select_related('blog').prefetch_related('images').filter(is_published=True).order_by('-published_at')
    )

    context_object_name = 'posts'

    template_name = 'app_blog/latest_posts.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=None, **kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = Profile.objects.get(user=self.request.user)
        return context

