def install(
    INSTALLED_APPS,
    REST_FRAMEWORK,
    MIDDLEWARE,
):
    INSTALLED_APPS.append("django_client_framework.apps.DefaultApp")
    MIDDLEWARE.append(
        "django_client_framework.exceptions.handlers.ConvertAPIExceptionToJsonResponse"
    )
    REST_FRAMEWORK[
        "EXCEPTION_HANDLER"
    ] = "django_client_framework.exceptions.handlers.dcf_exception_handler"
