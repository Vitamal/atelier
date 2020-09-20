from django import template
from django.template.loader import render_to_string

register = template.Library()


class AtelierEmailLinkNode(template.Node):
    def __init__(self, nodelist, url, linkstyle_context_variable, template_name):
        if url[0] in ('"', "'"):
            url = url[1:-1]
        else:
            # Assume we have a variable
            url = template.Variable(url)
        self.url = url
        self.nodelist = nodelist
        self.linkstyle_context_variable = linkstyle_context_variable
        self.template_name = template_name

    def render(self, context):
        output = self.nodelist.render(context)

        if isinstance(self.url, template.Variable):
            url = self.url.resolve(context)
        else:
            url = self.url
        if 'request' in context:
            request = context['request']
            url = request.build_absolute_uri(url)

        linkstyle = context.get(self.linkstyle_context_variable, '')
        return render_to_string(self.template_name, {
            'url': url,
            'label': output.strip(),
            'linkstyle': linkstyle
        }).strip()


def _atelier_email_link(parser, token, linkstyle_context_variable, template_name):
    try:
        tag_name, url = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one arguments" % token.contents.split()[0]
        )
    end_tag = 'end_{}'.format(tag_name)
    nodelist = parser.parse((end_tag,))
    parser.delete_first_token()
    return AtelierEmailLinkNode(nodelist=nodelist, url=url,
                                linkstyle_context_variable=linkstyle_context_variable,
                                template_name=template_name)


def _atelier_email_buttonlink(parser, token, linkstyle_context_variable):
    return _atelier_email_link(parser=parser, token=token,
                               linkstyle_context_variable=linkstyle_context_variable,
                               template_name='atelier_email/templatetags/atelier_email_buttonlink.django.html')


@register.tag
def atelier_email_link(parser, token):
    """
    Render a normal link.

    Examples::

        Url as string:

        .. code-block:: htmldjango

            {% load atelier_email_tags %}
            {% atelier_email_link "http://example.com" %}
                A link
            {% end_atelier_email_link %}

        Url as context variable:

        .. code-block:: htmldjango

            {% load atelier_email_tags %}
            {% atelier_email_link someurl %}
                A link
            {% end_atelier_email_link %}
    """
    return _atelier_email_link(parser=parser, token=token,
                               linkstyle_context_variable='link_style',
                               template_name='atelier_email/templatetags/atelier_email_link.django.html')


@register.tag
def atelier_email_primary_buttonlink(parser, token):
    """
    Render a link as a primary button.

    Examples::

        Url as string:

        .. code-block:: htmldjango

            {% load atelier_email_tags %}
            {% atelier_email_primary_buttonlink "http://example.com" %}
                A primary button link
            {% end_atelier_email_primary_buttonlink %}

        Url as context variable:

        .. code-block:: htmldjango

            {% load atelier_email_tags %}
            {% atelier_email_primary_buttonlink someurl %}
                A primary button link
            {% end_atelier_email_primary_buttonlink %}
    """
    return _atelier_email_buttonlink(parser, token,
                                     linkstyle_context_variable='primary_button_link_style')


@register.tag
def atelier_email_secondary_buttonlink(parser, token):
    """
    Render a link as a secondary button.

    Examples::

        Url as string:

        .. code-block:: htmldjango

            {% load atelier_email_tags %}
            {% atelier_email_secondary_buttonlink "http://example.com" %}
                A secondary button link
            {% end_atelier_email_secondary_buttonlink %}

        Url as context variable:

        .. code-block:: htmldjango

            {% load atelier_email_tags %}
            {% atelier_email_secondary_buttonlink someurl %}
                A secondary button link
            {% end_atelier_email_secondary_buttonlink %}
    """
    return _atelier_email_buttonlink(parser, token,
                                     linkstyle_context_variable='secondary_button_link_style')
