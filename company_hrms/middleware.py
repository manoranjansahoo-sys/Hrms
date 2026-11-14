import os
from django.urls import set_script_prefix, get_script_prefix


class SubpathRoutingMiddleware:
    """
    Enterprise Subpath Routing Middleware for HRMS.
    
    Ensures seamless operation both when deployed under a subpath (e.g. https://designlope.in/people/)
    and when testing locally on localhost/127.0.0.1 (without any subpath).
    
    1. Localhost / Offline Local Dev:
       - No subpath prefix is added. Everything resolves at root '/' (e.g. http://127.0.0.1:8000/).
       - If a developer visits http://127.0.0.1:8000/people/..., it is also smoothly supported.
       
    2. Deployed on designlope.in:
       - Automatically detects 'designlope.in' host, FORCE_SCRIPT_NAME='/people', or X-Forwarded-Prefix.
       - Sets SCRIPT_NAME to '/people' and script prefix to '/people/'.
       - Strips '/people' from incoming request.path_info if the reverse proxy forwarded it,
         so all standard Django urlpatterns match with 0 routing errors.
       - Guarantees that all {% url %}, reverse(), redirect(), and request.build_absolute_uri()
         automatically prepend '/people/' across the entire app.
       - Ensures all HTTP redirects (301/302) maintain the '/people' subpath.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        subpath = os.getenv("FORCE_SCRIPT_NAME", "").strip()

        # Automatic detection for production domain
        if not subpath and ("designlope.in" in host):
            subpath = "/people"

        # Also support reverse proxy headers (Nginx/Apache/Cloudflare/Passenger)
        forwarded_prefix = request.META.get("HTTP_X_FORWARDED_PREFIX", "").strip().rstrip("/")
        if forwarded_prefix:
            subpath = forwarded_prefix

        # Normalize subpath
        if subpath:
            subpath = "/" + subpath.strip("/")

        # Check if incoming request URL explicitly begins with /people (e.g. on localhost or unstripped proxy)
        if not subpath and (request.path_info.startswith("/people/") or request.path_info == "/people"):
            subpath = "/people"

        if subpath:
            # Strip subpath from path_info so Django URL patterns match root routes cleanly
            if request.path_info.startswith(subpath + "/") or request.path_info == subpath:
                request.path_info = request.path_info[len(subpath):] or "/"

            request.META["SCRIPT_NAME"] = subpath
            set_script_prefix(subpath + "/")
        else:
            set_script_prefix("/")

        response = self.get_response(request)

        # Ensure redirect locations on production domain preserve the subpath
        if subpath and response.has_header("Location"):
            location = response["Location"]
            if location.startswith("/") and not location.startswith(subpath + "/") and location != subpath:
                response["Location"] = subpath + location

        return response

