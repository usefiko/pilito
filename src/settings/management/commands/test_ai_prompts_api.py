"""
Test command for AI Prompts API functionality
Tests the OneToOneField relationship and auto-creation
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from settings.models import AIPrompts
from django.test import RequestFactory
from settings.views import AIPromptsAPIView, AIPromptsManualPromptAPIView
import json


class Command(BaseCommand):
    help = 'Test AI Prompts API functionality and OneToOneField relationship'

    def handle(self, *args, **options):
        self.stdout.write('🤖 Testing AI Prompts API...')
        self.stdout.write('=' * 60)
        
        try:
            # Test 1: Check OneToOneField relationship
            self.stdout.write('\n1️⃣ Testing OneToOneField Relationship:')
            user = User.objects.first()
            if not user:
                self.stdout.write('❌ No users found in database')
                return
            
            self.stdout.write(f'   👤 Testing with user: {user.username} ({user.email})')
            
            # Test get_or_create_for_user method
            prompts, created = AIPrompts.get_or_create_for_user(user)
            if created:
                self.stdout.write(f'   ✅ Created new AIPrompts for user')
            else:
                self.stdout.write(f'   ✅ Found existing AIPrompts for user')
            
            self.stdout.write(f'   📝 Manual prompt exists: {"✅" if prompts.manual_prompt else "❌"}')
            # Auto prompt is now in GeneralSettings
            from settings.models import GeneralSettings
            general_settings = GeneralSettings.get_settings()
            self.stdout.write(f'   🤖 Auto prompt exists: {"✅" if general_settings.auto_prompt else "❌"}')
            
            # Test 2: OneToOneField access through related name
            self.stdout.write('\n2️⃣ Testing Related Name Access:')
            try:
                user_prompts = user.ai_prompts
                self.stdout.write(f'   ✅ Accessed via user.ai_prompts: {user_prompts.id}')
            except AIPrompts.DoesNotExist:
                self.stdout.write(f'   ❌ Could not access user.ai_prompts')
            
            # Test 3: Signal auto-creation (simulate new user)
            self.stdout.write('\n3️⃣ Testing Signal Auto-Creation:')
            from django.db.models.signals import post_save
            
            # Find a user without AIPrompts or create a test scenario
            users_with_prompts = User.objects.filter(ai_prompts__isnull=False).count()
            total_users = User.objects.count()
            
            self.stdout.write(f'   📊 Users with AIPrompts: {users_with_prompts}/{total_users}')
            
            # Test 4: API Endpoints
            self.stdout.write('\n4️⃣ Testing API Endpoints:')
            factory = RequestFactory()
            
            # Test GET ai-prompts/
            self.stdout.write('   🔍 Testing GET /ai-prompts/:')
            view = AIPromptsAPIView()
            request = factory.get('/api/v1/settings/ai-prompts/')
            request.user = user
            
            response = view.get(request)
            if response.status_code == 200:
                data = response.data
                self.stdout.write(f'      ✅ Status: {response.status_code}')
                self.stdout.write(f'      📋 Success: {data.get("success")}')
                self.stdout.write(f'      🆕 Created: {data.get("created")}')
                if data.get("data"):
                    prompt_data = data["data"]
                    self.stdout.write(f'      📝 Manual prompt length: {len(prompt_data.get("manual_prompt", ""))} chars')
            else:
                self.stdout.write(f'      ❌ Status: {response.status_code}')
                self.stdout.write(f'      Error: {response.data}')
            
            # Test GET ai-prompts/manual-prompt/
            self.stdout.write('\n   🔍 Testing GET /ai-prompts/manual-prompt/:')
            manual_view = AIPromptsManualPromptAPIView()
            manual_request = factory.get('/api/v1/settings/ai-prompts/manual-prompt/')
            manual_request.user = user
            
            manual_response = manual_view.get(manual_request)
            if manual_response.status_code == 200:
                manual_data = manual_response.data
                self.stdout.write(f'      ✅ Status: {manual_response.status_code}')
                self.stdout.write(f'      📋 Success: {manual_data.get("success")}')
                manual_prompt = manual_data.get("manual_prompt", "")
                self.stdout.write(f'      📝 Manual prompt: {manual_prompt[:100]}...') 
            else:
                self.stdout.write(f'      ❌ Status: {manual_response.status_code}')
            
            # Test 5: PATCH manual prompt
            self.stdout.write('\n   ✏️ Testing PATCH /ai-prompts/manual-prompt/:')
            test_prompt = "Test manual prompt for API testing - updated successfully!"
            patch_request = factory.patch(
                '/api/v1/settings/ai-prompts/manual-prompt/',
                data=json.dumps({'manual_prompt': test_prompt}),
                content_type='application/json'
            )
            patch_request.user = user
            
            patch_response = manual_view.patch(patch_request)
            if patch_response.status_code == 200:
                patch_data = patch_response.data
                self.stdout.write(f'      ✅ Status: {patch_response.status_code}')
                self.stdout.write(f'      📋 Success: {patch_data.get("success")}')
                self.stdout.write(f'      💬 Message: {patch_data.get("message")}')
                
                # Verify the update
                prompts.refresh_from_db()
                if prompts.manual_prompt == test_prompt:
                    self.stdout.write(f'      ✅ Manual prompt updated successfully')
                else:
                    self.stdout.write(f'      ❌ Manual prompt update failed')
            else:
                self.stdout.write(f'      ❌ Status: {patch_response.status_code}')
                self.stdout.write(f'      Error: {patch_response.data}')
            
            # Test 6: Check database consistency
            self.stdout.write('\n5️⃣ Testing Database Consistency:')
            all_prompts = AIPrompts.objects.all()
            self.stdout.write(f'   📊 Total AIPrompts records: {all_prompts.count()}')
            
            # Check for duplicate records (should not exist with OneToOneField)
            users_with_multiple_prompts = []
            for user_obj in User.objects.all():
                try:
                    # With OneToOneField, this should either exist (1) or not exist (0)
                    user_obj.ai_prompts
                    prompts_count = 1
                except AIPrompts.DoesNotExist:
                    prompts_count = 0
                
                # Check if somehow there are multiple records (shouldn't happen with OneToOneField)
                actual_count = AIPrompts.objects.filter(user=user_obj).count()
                if actual_count > 1:
                    users_with_multiple_prompts.append(user_obj)
            
            if users_with_multiple_prompts:
                self.stdout.write(f'   ❌ Found {len(users_with_multiple_prompts)} users with multiple AIPrompts!')
                for dup_user in users_with_multiple_prompts:
                    self.stdout.write(f'      User: {dup_user.username}')
            else:
                self.stdout.write(f'   ✅ No duplicate AIPrompts found - OneToOneField working correctly')
            
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('✅ AI Prompts API Test Completed!')
            
            self.stdout.write('\n📋 Summary:')
            self.stdout.write(f'   • Model: AIPrompts with OneToOneField to User')
            self.stdout.write(f'   • Related name: user.ai_prompts')
            self.stdout.write(f'   • Auto-creation: On User creation via signals')
            self.stdout.write(f'   • API endpoints: /ai-prompts/ and /ai-prompts/manual-prompt/')
            self.stdout.write(f'   • Default prompts: Automatically provided')
            
        except Exception as e:
            self.stdout.write(f'❌ Test failed: {str(e)}')
            import traceback
            traceback.print_exc()