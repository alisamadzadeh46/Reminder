import jdatetime
from django import template

register = template.Library()

@register.filter
def jalali(dt, fmt="%Y/%m/%d %H:%M"):
    if not dt:
        return ""
    # dt is timezone-aware datetime
    return jdatetime.datetime.fromgregorian(datetime=dt).strftime(fmt)
