"""
End-to-End Test for Lean RAG v2.1
Tests complete flow: Knowledge Ingestion → Query → Response
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from AI_model.services.knowledge_ingestion_service import KnowledgeIngestionService
from AI_model.services.query_router import QueryRouter
from AI_model.services.context_retriever import ContextRetriever
from AI_model.services.token_budget_controller import TokenBudgetController
from AI_model.services.gemini_service import GeminiChatService
from AI_model.models import TenantKnowledge
from message.models import Conversation

User = get_user_model()


def print_header(title):
    print(f'\n{"="*70}')
    print(f'  {title}')
    print(f'{"="*70}\n')


def print_section(title):
    print(f'\n{"-"*70}')
    print(f'  {title}')
    print(f'{"-"*70}')


def test_lean_rag_e2e():
    """
    Complete End-to-End test
    """
    print_header('🚀 LEAN RAG v2.1 - END-TO-END TEST')
    
    # Step 1: Get test user
    print_section('Step 1: Select Test User')
    
    users = User.objects.filter(is_active=True)[:5]
    if not users:
        print('❌ No active users found!')
        return
    
    print(f'Found {users.count()} active users:')
    for i, user in enumerate(users, 1):
        print(f'  {i}. {user.username} ({user.email})')
    
    # Use first user for test
    test_user = users[0]
    print(f'\n✅ Using test user: {test_user.username}\n')
    
    # Step 2: Check existing knowledge
    print_section('Step 2: Check Existing Knowledge')
    
    existing_chunks = TenantKnowledge.objects.filter(user=test_user).count()
    print(f'Existing knowledge chunks: {existing_chunks}')
    
    if existing_chunks == 0:
        print('\n⚠️  No knowledge chunks found. Running ingestion...\n')
        
        # Run ingestion
        results = KnowledgeIngestionService.ingest_user_knowledge(
            user=test_user,
            sources=['faq', 'products', 'manual', 'website'],
            force_recreate=False
        )
        
        print(f'📊 Ingestion Results:')
        print(f'  FAQ:      {results["faq"]["chunks"]:>4} chunks')
        print(f'  Products: {results["products"]["chunks"]:>4} chunks')
        print(f'  Manual:   {results["manual"]["chunks"]:>4} chunks')
        print(f'  Website:  {results["website"]["chunks"]:>4} chunks')
        print(f'  Total:    {results["total_chunks"]:>4} chunks')
        
        if results['errors']:
            print(f'\n⚠️  Errors ({len(results["errors"])}):')
            for error in results['errors']:
                print(f'  • {error}')
    else:
        print(f'✅ Found {existing_chunks} existing chunks')
    
    # Step 3: Test Query Routing
    print_section('Step 3: Test Query Routing')
    
    test_queries = [
        "قیمت پلن حرفه‌ای چنده؟",
        "What are your products?",
        "چطور می‌تونم ثبت نام کنم؟",
        "Contact information please"
    ]
    
    for query in test_queries:
        routing = QueryRouter.route_query(query, user=test_user)
        print(f'\nQuery: "{query}"')
        print(f'  → Intent: {routing["intent"]} (confidence: {routing["confidence"]:.2f})')
        print(f'  → Primary source: {routing["primary_source"]}')
        print(f'  → Keywords matched: {routing["keywords_matched"][:3]}')
    
    # Step 4: Test Context Retrieval
    print_section('Step 4: Test Context Retrieval')
    
    test_query = test_queries[0]
    print(f'Query: "{test_query}"\n')
    
    routing = QueryRouter.route_query(test_query, user=test_user)
    
    retrieval_result = ContextRetriever.retrieve_context(
        query=test_query,
        user=test_user,
        primary_source=routing['primary_source'],
        secondary_sources=routing['secondary_sources'],
        primary_budget=routing['token_budgets']['primary'],
        secondary_budget=routing['token_budgets']['secondary']
    )
    
    print(f'📚 Retrieved {retrieval_result["total_chunks"]} chunks:')
    print(f'  Primary:   {len(retrieval_result["primary_context"])} chunks')
    print(f'  Secondary: {len(retrieval_result["secondary_context"])} chunks')
    print(f'  Method:    {retrieval_result["retrieval_method"]}')
    
    if retrieval_result['primary_context']:
        print(f'\n  Top result:')
        top = retrieval_result['primary_context'][0]
        print(f'    Title: {top["title"]}')
        print(f'    Score: {top.get("score", "N/A")}')
        print(f'    Preview: {top["content"][:150]}...')
    
    # Step 5: Test Token Budget Controller
    print_section('Step 5: Test Token Budget Controller')
    
    components = {
        'system_prompt': 'You are a helpful AI assistant. Answer questions accurately.',
        'conversation': '',
        'primary_context': retrieval_result['primary_context'],
        'secondary_context': retrieval_result['secondary_context'],
        'user_query': test_query
    }
    
    trimmed = TokenBudgetController.trim_to_budget(components)
    
    print(f'📊 Token Budget Allocation:')
    print(f'  System:    {trimmed["system_prompt_tokens"]:>4} tokens')
    print(f'  Query:     {trimmed["user_query_tokens"]:>4} tokens')
    print(f'  Conv:      {trimmed["conversation_tokens"]:>4} tokens')
    print(f'  Primary:   {trimmed["primary_context_tokens"]:>4} tokens')
    print(f'  Secondary: {trimmed["secondary_context_tokens"]:>4} tokens')
    print(f'  {"-"*30}')
    print(f'  Total:     {trimmed["total_tokens"]:>4} tokens (limit: 1500)')
    
    if trimmed['total_tokens'] <= 1500:
        print(f'\n✅ Within budget!')
    else:
        print(f'\n❌ EXCEEDED budget!')
    
    # Step 6: Test Full Prompt Building
    print_section('Step 6: Test Gemini Service (Full Integration)')
    
    # Create or get test conversation
    conversation = Conversation.objects.filter(user=test_user).first()
    
    gemini_service = GeminiChatService(user=test_user)
    
    if gemini_service.is_configured():
        print('✅ Gemini service configured')
        
        # Build prompt (don't generate response yet to save API calls)
        try:
            prompt = gemini_service._build_prompt(test_query, conversation)
            
            # Count tokens in final prompt
            from AI_model.services.token_budget_controller import TokenBudgetController
            prompt_tokens = TokenBudgetController._count_tokens(prompt)
            
            print(f'\n📝 Final Prompt:')
            print(f'  Length: {len(prompt)} chars')
            print(f'  Tokens: {prompt_tokens}')
            print(f'  Preview: {prompt[:200]}...\n')
            
            if prompt_tokens <= 1500:
                print('✅ Prompt within token limit!')
            else:
                print(f'⚠️  Prompt exceeds limit: {prompt_tokens} > 1500')
        
        except Exception as e:
            print(f'❌ Failed to build prompt: {e}')
    else:
        print('⚠️  Gemini service not configured (API key missing)')
        print('   Skipping full response generation test')
    
    # Summary
    print_header('📊 TEST SUMMARY')
    
    print('✅ Tested Components:')
    print('  1. Knowledge Ingestion Service')
    print('  2. Query Router (Intent Classification)')
    print('  3. Context Retriever (pgvector RAG)')
    print('  4. Token Budget Controller')
    print('  5. Gemini Service Integration')
    
    print(f'\n✅ Knowledge Base Stats:')
    stats = {
        'faq': TenantKnowledge.objects.filter(user=test_user, chunk_type='faq').count(),
        'products': TenantKnowledge.objects.filter(user=test_user, chunk_type='product').count(),
        'manual': TenantKnowledge.objects.filter(user=test_user, chunk_type='manual').count(),
        'website': TenantKnowledge.objects.filter(user=test_user, chunk_type='website').count(),
    }
    stats['total'] = sum(stats.values())
    
    print(f'  FAQ:      {stats["faq"]:>4} chunks')
    print(f'  Products: {stats["products"]:>4} chunks')
    print(f'  Manual:   {stats["manual"]:>4} chunks')
    print(f'  Website:  {stats["website"]:>4} chunks')
    print(f'  Total:    {stats["total"]:>4} chunks')
    
    print('\n🎉 END-TO-END TEST COMPLETE!\n')
    print('Next steps:')
    print('  1. Test with real customer queries')
    print('  2. Monitor token usage in production')
    print('  3. Fine-tune routing rules if needed')
    print('  4. Adjust token budgets based on usage patterns\n')


if __name__ == '__main__':
    try:
        test_lean_rag_e2e()
    except Exception as e:
        print(f'\n❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

