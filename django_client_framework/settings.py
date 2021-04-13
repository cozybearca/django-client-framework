def install(
    INSTALLED_APPS,
    REST_FRAMEWORK,
    MIDDLEWARE,
    AUTHENTICATION_BACKENDS,
):
    INSTALLED_APPS += [
        "rest_framework",
        "guardian",
        "django_client_framework.apps.DefaultApp",
    ]
    MIDDLEWARE += [
        "django_client_framework.exceptions.handlers.ConvertAPIExceptionToJsonResponse",
        "django_currentuser.middleware.ThreadLocalUserMiddleware",
    ]
    REST_FRAMEWORK[
        "EXCEPTION_HANDLER"
    ] = "django_client_framework.exceptions.handlers.dcf_exception_handler"
    AUTHENTICATION_BACKENDS += [
        "guardian.backends.ObjectPermissionBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]
