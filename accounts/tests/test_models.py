from accounts.models import Token
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):

    def test_user_is_valid_with_email_only(self):
        user = User(email='a@example.com')
        user.full_clean()  # should not raise

    def test_email_is_primary_key(self):
        user = User(email='a@example.com')
        self.assertEqual(user.pk, 'a@example.com')


class TokenModelTest(TestCase):

    def test_links_user_with_auto_generated_uid(self):
        token1 = Token.objects.create(email='a@example.com')
        token2 = Token.objects.create(email='a@example.com')
        self.assertNotEqual(token1.uid, token2.uid)
