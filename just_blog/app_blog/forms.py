from django import forms
from .models import Blog, Post
from django.utils.translation import gettext_lazy as _


class BlogForm(forms.ModelForm):

    class Meta:
        model = Blog
        fields = 'title', 'description',

    title = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'class': 'input blog-title-input'}))
    description = forms.CharField(max_length=256, widget=forms.Textarea(attrs={'class': 'input blog-descr-input',
                                                                               'cols': '50', 'rows': '5'}))


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = 'title', 'tag', 'content', 'images',

    title = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'class': 'input post-title-input'}))
    tag = forms.CharField(max_length=70, widget=forms.TextInput(attrs={'class': 'input'}))

    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
        label=_('Images')
    )

    content = forms.CharField(
        max_length=10**10,
        widget=forms.Textarea({"cols": "100", "rows": "10", 'class': 'input'}),
        label=_('Post content')
    )


class PostFileForm(forms.Form):
    file = forms.FileField(label=_('Csv file'),
                           widget=forms.ClearableFileInput(attrs={'id': 'csv_blog_id'}))
