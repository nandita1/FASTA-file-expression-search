from django import template
from django.utils.html import mark_safe
register = template.Library()

@register.filter
def highlight(text,arg):
    return mark_safe(text.replace(str(arg[0]),"<span style='background-color: red'>%s</span>" % str(arg[0])))
