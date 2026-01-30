from django import template

register = template.Library()


@register.filter
def dict_get(mapping, key):
    if not isinstance(mapping, dict):
        return ""
    return mapping.get(key, "")


@register.filter
def slot_value(mapping, args):
    if not isinstance(mapping, dict):
        return ""
    try:
        base, slot = args.split(",", 1)
    except ValueError:
        return ""
    key = f"{base}_{slot}"
    return mapping.get(key, "")


@register.filter
def slot_error(mapping, args):
    return slot_value(mapping, args)


@register.simple_tag
def slot_value_for(mapping, base, slot):
    if not isinstance(mapping, dict):
        return ""
    key = f"{base}_{slot}"
    return mapping.get(key, "")


@register.simple_tag
def slot_error_for(mapping, base, slot):
    if not isinstance(mapping, dict):
        return ""
    key = f"{base}_{slot}"
    return mapping.get(key, "")


@register.simple_tag
def slot_value_for(mapping, base, slot):
    if not isinstance(mapping, dict):
        return ""
    key = f"{base}_{slot}"
    return mapping.get(key, "")
