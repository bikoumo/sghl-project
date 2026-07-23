import json
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='secret123',
            role='DOCTOR',
            is_mfa_enabled=True,
        )

    def test_login_rejects_unknown_email_with_401(self):
        response = self.client.post(
            '/api/v2/auth/login/',
            data=json.dumps({'username': 'unknown@example.com', 'password': 'secret123'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn('Email ou mot de passe incorrect', response.json()['detail'])

    def test_login_rejects_wrong_password_with_401(self):
        response = self.client.post(
            '/api/v2/auth/login/',
            data=json.dumps({'username': 'doctor@example.com', 'password': 'wrong-password'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn('Email ou mot de passe incorrect', response.json()['detail'])

    def test_login_returns_mfa_step_on_valid_credentials(self):
        response = self.client.post(
            '/api/v2/auth/login/',
            data=json.dumps({'username': 'doctor@example.com', 'password': 'secret123'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['requires_mfa'])
        self.assertEqual(payload['username'], 'doctor1')
        # Sans credentials SMTP : fallback UI avec le code à 6 chiffres
        self.assertFalse(payload.get('email_sent'))
        self.assertIsNotNone(payload.get('fallback_code'))
        self.assertEqual(len(payload['fallback_code']), 6)
        self.assertTrue(payload['fallback_code'].isdigit())
        self.assertEqual(payload['message'], 'Code généré')

    def test_login_returns_token_when_mfa_disabled(self):
        self.user.is_mfa_enabled = False
        self.user.save(update_fields=['is_mfa_enabled'])

        response = self.client.post(
            '/api/v2/auth/login/',
            data=json.dumps({'username': 'doctor@example.com', 'password': 'secret123'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['requires_mfa'])
        self.assertEqual(payload['status'], 'success')
        self.assertIn('token', payload)
        self.assertTrue(payload['token'])


class VerifyMfaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='secret123',
            role='DOCTOR',
            is_mfa_enabled=True,
        )
        cache.set(f"mfa_{self.user.id}", "123456", timeout=300)

    def test_verify_mfa_rejects_wrong_code_with_400(self):
        response = self.client.post(
            '/api/v2/auth/verify-mfa/',
            data=json.dumps({'username': self.user.username, 'code': '000000'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Code incorrect', response.json()['detail'])

    def test_verify_mfa_returns_signed_token_on_success(self):
        response = self.client.post(
            '/api/v2/auth/verify-mfa/',
            data=json.dumps({'username': self.user.username, 'code': '123456'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())
        self.assertTrue(response.json()['token'])
