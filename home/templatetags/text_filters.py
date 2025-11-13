# home/templatetags/text_filters.py
from django import template

register = template.Library()

@register.filter
def espaciar(value):
    """
    Convierte TEXTO_EN_MAYUSCULAS a 'Texto En Mayusculas'
    reemplazando guiones bajos por espacios.
    """
    if not isinstance(value, str):
        return value
    return value.replace("_", " ").title()

