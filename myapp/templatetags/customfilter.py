from django import template
from django.utils.html import mark_safe
import re
register = template.Library()

@register.filter
def highlight(text,args):
    for arg in args:
    #new_text=''
        text = text.replace(arg,"<span style='background-color: red'>%s</span>" % arg)
    #locations = [m.start() for m in re.finditer(arg,text)]
    #i=0
    #for location in locations:
    #    new_text+=text[i:location]
    #    new_text+="<span style='background-color: red'>%s</span>" % arg
    #    new_text+=text[len(arg)+location:len(text)]
    #    i=location
    return mark_safe(text)
