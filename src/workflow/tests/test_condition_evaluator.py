"""
Tests for condition evaluator utilities
"""

import unittest
from workflow.utils.condition_evaluator import (
    get_nested_value,
    evaluate_single_condition,
    evaluate_condition_group,
    evaluate_conditions,
    substitute_template_placeholders
)


class TestConditionEvaluator(unittest.TestCase):
    """Test condition evaluation functions"""
    
    def setUp(self):
        self.test_context = {
            'user': {
                'id': '123',
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone_number': '+1234567890',
                'description': 'Premium customer from New York',
                'tags': ['premium', 'active'],
                'profile': {
                    'age': 30,
                    'city': 'New York'
                }
            },
            'event': {
                'type': 'MESSAGE_RECEIVED',
                'data': {
                    'content': 'Hello world',
                    'timestamp': '2024-01-01T00:00:00Z'
                }
            }
        }
    
    def test_get_nested_value(self):
        """Test nested value extraction"""
        # Test simple path
        self.assertEqual(get_nested_value(self.test_context, 'user.id'), '123')
        
        # Test nested path
        self.assertEqual(get_nested_value(self.test_context, 'user.profile.age'), 30)
        
        # Test array access
        self.assertEqual(get_nested_value(self.test_context, 'user.tags.0'), 'premium')
        
        # Test missing path
        self.assertIsNone(get_nested_value(self.test_context, 'user.missing'))
        
        # Test with default
        self.assertEqual(get_nested_value(self.test_context, 'user.missing', 'default'), 'default')
    
    def test_evaluate_single_condition_equals(self):
        """Test equals operator"""
        condition = {
            'field': 'user.email',
            'operator': 'equals',
            'value': 'test@example.com'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        condition['value'] = 'other@example.com'
        self.assertFalse(evaluate_single_condition(condition, self.test_context))
    
    def test_evaluate_single_condition_contains(self):
        """Test contains operator"""
        condition = {
            'field': 'event.data.content',
            'operator': 'contains',
            'value': 'Hello'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        condition['value'] = 'goodbye'
        self.assertFalse(evaluate_single_condition(condition, self.test_context))
    
    def test_evaluate_single_condition_icontains(self):
        """Test case-insensitive contains operator"""
        condition = {
            'field': 'event.data.content',
            'operator': 'icontains',
            'value': 'HELLO'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
    
    def test_evaluate_single_condition_in(self):
        """Test in operator"""
        condition = {
            'field': 'user.tags.0',
            'operator': 'in',
            'value': ['premium', 'basic']
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        condition['value'] = ['basic', 'trial']
        self.assertFalse(evaluate_single_condition(condition, self.test_context))
    
    def test_evaluate_single_condition_greater(self):
        """Test greater than operator"""
        condition = {
            'field': 'user.profile.age',
            'operator': 'greater',
            'value': 25
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        condition['value'] = 35
        self.assertFalse(evaluate_single_condition(condition, self.test_context))
    
    def test_evaluate_condition_group_and(self):
        """Test AND condition group"""
        conditions = [
            {'field': 'user.first_name', 'operator': 'equals', 'value': 'John'},
            {'field': 'user.profile.age', 'operator': 'greater', 'value': 25}
        ]
        
        self.assertTrue(evaluate_condition_group(conditions, 'and', self.test_context))
        
        # Make one condition fail
        conditions[0]['value'] = 'Jane'
        self.assertFalse(evaluate_condition_group(conditions, 'and', self.test_context))
    
    def test_evaluate_condition_group_or(self):
        """Test OR condition group"""
        conditions = [
            {'field': 'user.first_name', 'operator': 'equals', 'value': 'Jane'},  # This will fail
            {'field': 'user.profile.age', 'operator': 'greater', 'value': 25}     # This will pass
        ]
        
        self.assertTrue(evaluate_condition_group(conditions, 'or', self.test_context))
        
        # Make both conditions fail
        conditions[1]['value'] = 35
        self.assertFalse(evaluate_condition_group(conditions, 'or', self.test_context))
    
    def test_evaluate_conditions_complex(self):
        """Test complex condition evaluation"""
        condition_config = {
            'operator': 'and',
            'conditions': [
                {'field': 'user.email', 'operator': 'contains', 'value': '@example.com'},
                {
                    'operator': 'or',
                    'conditions': [
                        {'field': 'user.tags.0', 'operator': 'equals', 'value': 'premium'},
                        {'field': 'user.profile.age', 'operator': 'greater', 'value': 25}
                    ]
                }
            ]
        }
        
        self.assertTrue(evaluate_conditions(condition_config, self.test_context))
    
    def test_substitute_template_placeholders_string(self):
        """Test template placeholder substitution in strings"""
        template = "Hello {{user.first_name}} {{user.last_name}}!"
        result = substitute_template_placeholders(template, self.test_context)
        self.assertEqual(result, "Hello John Doe!")
    
    def test_substitute_template_placeholders_dict(self):
        """Test template placeholder substitution in dictionaries"""
        template = {
            'subject': 'Welcome {{user.first_name}}!',
            'message': 'Your email is {{user.email}}',
            'age': '{{user.profile.age}}'
        }
        result = substitute_template_placeholders(template, self.test_context)
        
        expected = {
            'subject': 'Welcome John!',
            'message': 'Your email is test@example.com',
            'age': '30'
        }
        self.assertEqual(result, expected)
    
    def test_substitute_template_placeholders_list(self):
        """Test template placeholder substitution in lists"""
        template = [
            'Hello {{user.first_name}}',
            'Your age is {{user.profile.age}}'
        ]
        result = substitute_template_placeholders(template, self.test_context)
        
        expected = [
            'Hello John',
            'Your age is 30'
        ]
        self.assertEqual(result, expected)
    
    def test_user_phone_number_field(self):
        """Test that phone_number field is accessible in conditions"""
        condition = {
            'field': 'user.phone_number',
            'operator': 'equals',
            'value': '+1234567890'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        # Test with contains operator
        condition = {
            'field': 'user.phone_number',
            'operator': 'contains',
            'value': '1234'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        # Test is_not_empty operator
        condition = {
            'field': 'user.phone_number',
            'operator': 'is_not_empty',
            'value': None
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
    
    def test_user_description_field(self):
        """Test that description field is accessible in conditions"""
        condition = {
            'field': 'user.description',
            'operator': 'contains',
            'value': 'Premium'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
        
        # Test case-insensitive search
        condition = {
            'field': 'user.description',
            'operator': 'icontains',
            'value': 'premium'
        }
        self.assertTrue(evaluate_single_condition(condition, self.test_context))
    
    def test_user_fields_template_substitution(self):
        """Test template substitution with new user fields"""
        template = "Contact {{user.first_name}} at {{user.phone_number}}"
        result = substitute_template_placeholders(template, self.test_context)
        self.assertEqual(result, "Contact John at +1234567890")
        
        template = "User info: {{user.description}}"
        result = substitute_template_placeholders(template, self.test_context)
        self.assertEqual(result, "User info: Premium customer from New York")


if __name__ == '__main__':
    unittest.main()
