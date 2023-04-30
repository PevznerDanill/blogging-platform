from django import template
import re

register = template.Library()


@register.filter(name="break_tags")
def break_tags(value):
    pattern = '.#'
    value = re.sub(pattern, '<br>#', value)
    return value
