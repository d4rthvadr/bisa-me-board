from .theme import get_request_theme


def theme(request):
    ui_theme = get_request_theme(request)
    return {
        'ui_theme': ui_theme,
        'ui_theme_is_dark': ui_theme == 'dark',
    }
