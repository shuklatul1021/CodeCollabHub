from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile

class AccountsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    def test_profile_creation(self):
        # Test that profile is automatically created for new user
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_login_view(self):
        # Test login functionality
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after login

    def test_register_view(self):
        # Test registration functionality
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newuserpassword',
            'password2': 'newuserpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())
