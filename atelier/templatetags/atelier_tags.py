from django import template

register = template.Library()


@register.simple_tag()
def alias(obj):
    return obj


@register.simple_tag
def define(val=None):
    return val


@register.simple_tag
def url_prepend(request, name, value, distinct=True, exclude=None, clear_filters=False):
    """
    prepend given parameter to request querystring
    :param request: request
    :param name: string, parameter name
    :param value: string, parameter value
    :param distinct: boolean, clear existing values for given parameter
    :param exclude: string, string of parameters names to remove, separated by space
    :param clear_filters: boolean, clear parameters starting with 'filter_'
    :return:
    """
    new_querystring = f"?{name}={value}" if name else "?"
    querystring = request.GET.urlencode()
    if not querystring:
        return new_querystring

    exclude = [] if exclude is None else exclude.split()
    params = querystring.split('&')
    if distinct:
        exclude.append(name)
    else:
        params = filter(lambda p: p != f"{name}={value}", params)
    if clear_filters:
        params = filter(lambda p: not p.startswith('filter_'), params)
    filtered_querystring = '&'.join(filter(lambda p: p.split('=')[0] not in exclude, params))
    return f"{new_querystring}&{filtered_querystring}"

