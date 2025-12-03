from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsAPITest(APITestCase):
    def setUp(self):
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123',
            'gender': 'M'  # required by your model
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)

    def test_user_login(self):
        # Register the user first via API
        self.client.post(self.register_url, self.user_data, format='json')

        # Login using email, not username
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
    
    def test_registration_with_valid_affiliate_code(self):
        """Test registration with a valid affiliate code"""
        # First, create a referrer user
        referrer = User.objects.create_user(
            username='referrer',
            email='referrer@example.com',
            password='password123',
            gender='M'
        )
        referrer_invite_code = referrer.invite_code
        initial_wallet = referrer.wallet_balance
        
        # Register a new user with the referrer's invite code
        new_user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'affiliate': referrer_invite_code
        }
        
        response = self.client.post(self.register_url, new_user_data, format='json')
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user_data includes affiliate fields
        user_data = response.data.get('user_data')
        self.assertIsNotNone(user_data)
        self.assertIn('invite_code', user_data)
        self.assertIn('referred_by', user_data)
        self.assertIn('referrer_username', user_data)
        self.assertIn('wallet_balance', user_data)
        
        # Check that affiliate was applied
        self.assertEqual(user_data['referred_by'], referrer.id)
        self.assertEqual(user_data['referrer_username'], 'referrer')
        
        # Check affiliate_info in response
        affiliate_info = response.data.get('affiliate_info')
        self.assertIsNotNone(affiliate_info)
        self.assertEqual(affiliate_info['affiliate_code_provided'], referrer_invite_code)
        self.assertTrue(affiliate_info['affiliate_applied'])
        self.assertIsNone(affiliate_info['error'])
        
        # Check referrer information in response
        referrer_info = affiliate_info.get('referrer')
        self.assertIsNotNone(referrer_info)
        self.assertEqual(referrer_info['id'], referrer.id)
        self.assertEqual(referrer_info['username'], 'referrer')
        self.assertEqual(referrer_info['invite_code'], referrer_invite_code)
        
        # Verify database was updated correctly
        referrer.refresh_from_db()
        self.assertEqual(referrer.wallet_balance, initial_wallet + 10)
        
        new_user = User.objects.get(email='newuser@example.com')
        self.assertEqual(new_user.referred_by, referrer)
        
        # Email confirmation status should be in response
        # (it may fail if SMTP is not configured in tests, but registration should succeed)
        self.assertIn('email_confirmation_sent', response.data)
    
    def test_registration_with_invalid_affiliate_code(self):
        """Test registration with an invalid affiliate code"""
        new_user_data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'securepass123',
            'affiliate': '9999'  # Invalid code
        }
        
        response = self.client.post(self.register_url, new_user_data, format='json')
        
        # Registration should still succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user_data shows no referrer
        user_data = response.data.get('user_data')
        self.assertIsNone(user_data['referred_by'])
        self.assertIsNone(user_data['referrer_username'])
        
        # Check affiliate_info shows error
        affiliate_info = response.data.get('affiliate_info')
        self.assertIsNotNone(affiliate_info)
        self.assertEqual(affiliate_info['affiliate_code_provided'], '9999')
        self.assertFalse(affiliate_info['affiliate_applied'])
        self.assertEqual(affiliate_info['error'], 'Invalid affiliate code')
        self.assertIsNone(affiliate_info['referrer'])
    
    def test_registration_without_affiliate_code(self):
        """Test registration without any affiliate code"""
        new_user_data = {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'securepass123'
        }
        
        response = self.client.post(self.register_url, new_user_data, format='json')
        
        # Registration should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user_data still includes affiliate fields
        user_data = response.data.get('user_data')
        self.assertIsNotNone(user_data['invite_code'])  # User gets their own code
        self.assertIsNone(user_data['referred_by'])
        self.assertIsNone(user_data['referrer_username'])
        self.assertEqual(user_data['wallet_balance'], '0.00')
        
        # affiliate_info should not be in response
        self.assertNotIn('affiliate_info', response.data)