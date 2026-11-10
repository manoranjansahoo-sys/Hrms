import time
from unittest.mock import patch

from django.test import SimpleTestCase, Client, override_settings
from django.urls import reverse


@override_settings(
    GOOGLE_CLIENT_ID='test-client',
    SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
)
class GoogleSignInTests(SimpleTestCase):
    def setUp(self):
        self.verify_url = reverse('recruitment:google_verify')
        session = self.client.session
        session['candidate_google_nonce'] = 'test-nonce'
        session.save()
        self.client.cookies['sessionid'] = session.session_key

    def claims(self, **changes):
        return dict({
            'sub': 'google-user', 'email': 'candidate@gmail.com',
            'name': 'Candidate', 'email_verified': True,
            'nonce': 'test-nonce', 'exp': time.time() + 3600,
        }, **changes)

    @patch('recruitment.google_auth.id_token.verify_oauth2_token')
    def test_verified_google_identity_is_saved_and_nonce_consumed(self, verify):
        verify.return_value = self.claims()
        response = self.client.post(self.verify_url, {'credential': 'signed-token'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(verify.call_args.args[2], 'test-client')
        self.assertEqual(self.client.session['candidate_google_identity']['sub'], 'google-user')
        self.assertNotIn('candidate_google_nonce', self.client.session)
        self.assertEqual(self.client.post(self.verify_url, {'credential': 'signed-token'}).status_code, 400)

    @patch('recruitment.google_auth.id_token.verify_oauth2_token')
    def test_invalid_signature_nonce_and_unverified_email_are_rejected(self, verify):
        verify.side_effect = ValueError('Invalid signature')
        self.assertEqual(self.client.post(self.verify_url, {'credential': 'fake'}).status_code, 401)
        verify.side_effect = None
        for claims in (self.claims(nonce='another-session'), self.claims(email_verified=False)):
            verify.return_value = claims
            self.assertEqual(self.client.post(self.verify_url, {'credential': 'token'}).status_code, 401)
            self.assertNotIn('candidate_google_identity', self.client.session)

    def test_application_requires_google_session_before_accessing_database(self):
        response = self.client.post(reverse('recruitment:candidate_fast_apply'), {'email': 'fake@gmail.com'})
        self.assertEqual(response.status_code, 403)

    def test_application_rejects_changed_email(self):
        session = self.client.session
        session['candidate_google_identity'] = self.claims(expires_at=time.time() + 3600)
        session.save()
        self.client.cookies['sessionid'] = session.session_key
        response = self.client.post(reverse('recruitment:candidate_fast_apply'), {'email': 'other@gmail.com'})
        self.assertEqual(response.status_code, 403)

    def test_verification_requires_csrf_and_post(self):
        self.assertEqual(self.client.get(self.verify_url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.verify_url, {'credential': 'token'}).status_code, 403)

    def test_expired_session_cannot_submit(self):
        session = self.client.session
        session['candidate_google_identity'] = self.claims(expires_at=time.time() - 1)
        session.save()
        self.client.cookies['sessionid'] = session.session_key
        response = self.client.post(reverse('recruitment:candidate_fast_apply'), {'email': 'candidate@gmail.com'})
        self.assertEqual(response.status_code, 403)

    def test_reset_removes_identity(self):
        response = self.client.post(reverse('recruitment:google_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('candidate_google_nonce', self.client.session)
