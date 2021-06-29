from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def template_filename(context):
    '''Returns template filename with the extension'''
    return context.template_name


@register.simple_tag(takes_context=True)
def user_class(context):
    '''Defines a class-string based on permissions'''
    usr = context.request.user
    cls = '{}{}'.format(
        'super' if usr.is_superuser else '',
        'staff'if usr.is_staff else '')
    return cls


@register.simple_tag(takes_context=True)
def user_initials(context):
    '''Returns the initials of the logged-in user, or blanks'''
    usr = context.request.user
    chf = usr.first_name[0] if len(usr.first_name) else ' '
    chl = usr.last_name[0] if len(usr.last_name) else ' '
    return ''.join([chf, chl]).upper()
