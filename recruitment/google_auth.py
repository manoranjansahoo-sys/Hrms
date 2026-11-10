import secrets
import time

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token


def verified_identity(request):
    identity = request.session.get('candidate_google_identity', {})
    if identity.get('expires_at', 0) > time.time():
        return identity
    request.session.pop('candidate_google_identity', None)
    return None


def sign_in_config(request):
    nonce = request.session.get('candidate_google_nonce')
    if not nonce:
        nonce = secrets.token_urlsafe(32)
        request.session['candidate_google_nonce'] = nonce
    return {'client_id': settings.GOOGLE_CLIENT_ID, 'nonce': nonce}


@require_POST
def google_verify(request):
    if not settings.GOOGLE_CLIENT_ID:
        return JsonResponse({'error': 'Google sign-in is not configured.'}, status=503)
    credential = request.POST.get('credential', '')
    nonce = request.session.get('candidate_google_nonce')
    if not credential or not nonce or len(credential) > 16384:
        return JsonResponse({'error': 'Please reload and sign in with Google.'}, status=400)
    try:
        claims = id_token.verify_oauth2_token(credential, Request(), settings.GOOGLE_CLIENT_ID)
        if (not secrets.compare_digest(str(claims.get('nonce', '')), nonce)
                or claims.get('email_verified') is not True
                or not claims.get('email') or not claims.get('sub')):
            raise ValueError('Invalid identity')
    except (ValueError, GoogleAuthError):
        return JsonResponse({'error': 'Google verification failed. Please try again.'}, status=401)
    request.session.cycle_key()
    identity = {
        'sub': claims['sub'],
        'email': claims['email'].strip().lower(),
        'name': claims.get('name') or claims['email'],
        'expires_at': min(claims['exp'], time.time() + 3600),
    }
    request.session['candidate_google_identity'] = identity
    request.session.pop('candidate_google_nonce', None)
    return JsonResponse({'name': identity['name'], 'email': identity['email']})


@require_POST
def google_reset(request):
    request.session.pop('candidate_google_identity', None)
    request.session.pop('candidate_google_nonce', None)
    return JsonResponse({'ok': True})
