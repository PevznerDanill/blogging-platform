from django import template
import re
from django.utils.safestring import SafeString
from app_blog.models import Post
from app_auth.models import Profile
from django.db.models import QuerySet

register = template.Library()


@register.filter(name="break_tags", is_safe=True)
def break_tags(value: str) -> str:
    """
    Adds <br> tag before every # symbol except the first one.
    """
    pattern = '.#'
    value = re.sub(pattern, '<br>#', value)
    return value


@register.filter(is_safe=True)
def change_class_for_post_new(safe_string: SafeString) -> str:
    """
    Adds classes to the elements.
    """
    div_pattern = r'<div>'
    label_pattern = r'<label for="id_images">'
    label_text_pattern = r'id_images">\w+\s*\w+:</label'
    safe_string = re.sub(div_pattern, '<div class="form-post-box">', safe_string)
    safe_string = re.sub(label_pattern, '<label class="btn register__btn" for="id_images">', safe_string)
    safe_string = re.sub(label_text_pattern, lambda match: match.group(0).replace(':', ''), safe_string)

    errors_pattern = r'class="errorlist"'
    safe_string = re.sub(errors_pattern, 'class="errorlist list-reset"', safe_string)

    return safe_string


@register.filter(is_safe=True)
def change_class_for_cvs_new(safe_string: SafeString) -> str:
    """
    Adds classes to the elements.
    """
    div_pattern = r'<div>'
    label_pattern = r'<label for="csv_blog_id">'
    label_text_pattern = r'csv_blog_id">\w+\s*\w+:</label'
    safe_string = re.sub(div_pattern, '<div class="form-post-box inline-block">', safe_string)
    safe_string = re.sub(label_pattern, '<label class="btn register__btn" for="csv_blog_id">', safe_string)
    safe_string = re.sub(label_text_pattern, lambda match: match.group(0).replace(':', ''), safe_string)

    return safe_string


@register.filter(name="cur_profile")
def cur_profile(post: Post, profiles: QuerySet) -> Profile:
    """
    Goes through the queryset of Profile instances and returns the one that
    matches the passed Post instance
    """
    for profile in profiles:
        if post.profile == profile:
            return profile
