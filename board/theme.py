from django.utils.http import url_has_allowed_host_and_scheme


THEME_COOKIE_NAME = 'board_theme'
DEFAULT_THEME = 'light'
SUPPORTED_THEMES = {'light', 'dark'}


def normalize_theme(value):
    return value if value in SUPPORTED_THEMES else DEFAULT_THEME


def get_request_theme(request):
    return normalize_theme(request.COOKIES.get(THEME_COOKIE_NAME))


def get_safe_redirect_target(request, fallback):
    candidate = request.POST.get('next') or request.GET.get('next') or fallback
    if url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback
