from django import forms
from .models import Blog, Post
from django.utils.translation import gettext_lazy as _


class BlogForm(forms.ModelForm):
    """
    A form for Blog model.
    """

    class Meta:
        model = Blog
        fields = 'title', 'description',

    title = forms.CharField(
        max_length=128,
        widget=forms.TextInput(attrs={'class': 'input blog-title-input'}),
        label=_('Title')
    )
    description = forms.CharField(
        max_length=256,
        widget=forms.Textarea(attrs={'class': 'input blog-descr-input','cols': '50', 'rows': '5'}),
        label=_('Description')
    )


class PostForm(forms.ModelForm):
    """
    A form for Post model.
    """
    class Meta:
        model = Post
        fields = 'title', 'tag', 'content', 'images',

    title = forms.CharField(
        max_length=128,
        widget=forms.TextInput(attrs={'class': 'input post-title-input'}),
        label=_('Title')
    )
    tag = forms.CharField(
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'input'}),
        label=_('Tag'),
    )

    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
        label=_('Upload images'),
    )

    content = forms.CharField(
        max_length=10**10,
        widget=forms.Textarea({"cols": "100", "rows": "10", 'class': 'input'}),
        label=_('Post content'),
    )


class PostFileForm(forms.Form):
    """
    A form for the creation of a new Post instance with a csv file.
    """
    file = forms.FileField(
        label=_('Csv file'),
        widget=forms.ClearableFileInput(attrs={'id': 'csv_blog_id'})
    )
