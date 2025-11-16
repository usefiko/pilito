"""
Test for URL-only message guard
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from AI_model.services.message_integration import _is_only_url


class TestURLOnlyGuard:
    """Test cases for _is_only_url() function"""
    
    def test_only_url_simple(self):
        """Test: Simple URL only"""
        assert _is_only_url("https://example.com") == True
        
    def test_only_url_with_punctuation(self):
        """Test: URL with minimal punctuation"""
        assert _is_only_url("https://example.com.") == True
        assert _is_only_url("https://example.com?") == True
        assert _is_only_url("https://example.com،") == True
        
    def test_multiple_urls_only(self):
        """Test: Multiple URLs without meaningful text"""
        assert _is_only_url("https://example.com https://test.com") == True
        
    def test_url_with_question(self):
        """Test: URL + meaningful question (should NOT trigger guard)"""
        assert _is_only_url("https://example.com\nاین چیه؟") == False
        assert _is_only_url("https://example.com این چیست؟") == False
        assert _is_only_url("https://example.com what is this?") == False
        
    def test_url_with_text(self):
        """Test: URL + explanatory text (should NOT trigger guard)"""
        assert _is_only_url("https://example.com\nمیخوام این رو بخرم") == False
        assert _is_only_url("نگاه کن به این: https://example.com") == False
        
    def test_text_only_no_url(self):
        """Test: Text without URL"""
        assert _is_only_url("سلام چطوری؟") == False
        assert _is_only_url("درباره محصولاتتون بگو") == False
        
    def test_empty_or_none(self):
        """Test: Empty or None input"""
        assert _is_only_url("") == False
        assert _is_only_url(None) == False
        assert _is_only_url("   ") == False
        
    def test_url_with_short_text(self):
        """Test: URL + very short text (< 10 chars non-URL)"""
        # "ok" = 2 chars → should trigger guard
        assert _is_only_url("https://example.com ok") == True
        # "خیلی خوب" = ~8 chars → should trigger guard
        assert _is_only_url("https://example.com خوب") == True
        # "خیلی خوب است" = > 10 chars → should NOT trigger guard
        assert _is_only_url("https://example.com خیلی خوب است") == False


if __name__ == '__main__':
    # Quick manual test
    test = TestURLOnlyGuard()
    
    print("✅ Testing _is_only_url() function...\n")
    
    # Test 1: Only URL
    test.test_only_url_simple()
    print("✅ Test 1: Simple URL only - PASSED")
    
    # Test 2: URL + punctuation
    test.test_only_url_with_punctuation()
    print("✅ Test 2: URL with punctuation - PASSED")
    
    # Test 3: Multiple URLs
    test.test_multiple_urls_only()
    print("✅ Test 3: Multiple URLs - PASSED")
    
    # Test 4: URL + question
    test.test_url_with_question()
    print("✅ Test 4: URL with question - PASSED")
    
    # Test 5: URL + text
    test.test_url_with_text()
    print("✅ Test 5: URL with text - PASSED")
    
    # Test 6: No URL
    test.test_text_only_no_url()
    print("✅ Test 6: Text without URL - PASSED")
    
    # Test 7: Empty input
    test.test_empty_or_none()
    print("✅ Test 7: Empty/None input - PASSED")
    
    # Test 8: URL + short text
    test.test_url_with_short_text()
    print("✅ Test 8: URL with short text - PASSED")
    
    print("\n🎉 All tests PASSED!")

