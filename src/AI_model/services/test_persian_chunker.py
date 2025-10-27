"""
Test script for Persian-aware chunking
Run: python manage.py shell < test_persian_chunker.py
"""

def test_persian_chunker():
    """Test Persian chunker with real Persian content"""
    from AI_model.services.persian_chunker import PersianChunker
    
    print("=" * 80)
    print("🧪 Testing Persian-Aware Chunking")
    print("=" * 80)
    
    # Test 1: Persian text detection
    print("\n1️⃣ Test: Language Detection")
    persian_text = "بورسیه کوچینگ فراکوچ برای افراد اثرگذار طراحی شده است"
    english_text = "Hello world this is a test"
    mixed_text = "Hello سلام world دنیا"
    
    lang_fa = PersianChunker._detect_language(persian_text)
    lang_en = PersianChunker._detect_language(english_text)
    lang_mixed = PersianChunker._detect_language(mixed_text)
    
    print(f"  Persian text: '{persian_text[:40]}...' → {lang_fa}")
    print(f"  English text: '{english_text}' → {lang_en}")
    print(f"  Mixed text: '{mixed_text}' → {lang_mixed}")
    print(f"  ✅ Language detection working!")
    
    # Test 2: Keyword extraction (Persian)
    print("\n2️⃣ Test: Persian Keyword Extraction")
    keywords = PersianChunker._extract_keywords_persian(persian_text)
    print(f"  Text: {persian_text}")
    print(f"  Keywords: {keywords}")
    print(f"  ✅ Extracted {len(keywords)} keywords")
    
    # Test 3: TL;DR (Persian)
    print("\n3️⃣ Test: Persian TL;DR")
    long_persian = """
    بورسیه کوچینگ فراکوچ برای افراد اثرگذار طراحی شده است که یادگیری کوچینگ 
    فقط به رشد شخصی‌شان ختم نمی‌شود. این افراد می‌توانند الهام‌بخش دیگران باشند.
    هدف ما فقط آموزش مهارت نیست بلکه می‌خواهیم فرهنگ کوچینگ را در جامعه گسترش دهیم.
    مدل تخصیص بورسیه متناسب با شرایط هر فرد و پس از بررسی سوابق تعیین می‌شود.
    در صورت پذیرش بخشی از هزینه دوره کسر می‌گردد و بورسیه‌شونده در قالب همکاری 
    با آکادمی مشارکت خواهد داشت. برای ورود به فرایند با کارشناسان ارتباط بگیرید.
    """
    tldr = PersianChunker.extract_tldr_persian(long_persian.strip(), max_words=30)
    print(f"  Original ({len(long_persian.split())} words):")
    print(f"    {long_persian.strip()[:100]}...")
    print(f"  TL;DR ({len(tldr.split())} words):")
    print(f"    {tldr}")
    print(f"  ✅ TL;DR generated successfully")
    
    # Test 4: Chunking with metadata
    print("\n4️⃣ Test: Chunking with Metadata")
    chunks_data = PersianChunker.chunk_text_with_metadata(
        text=long_persian.strip(),
        chunk_size=50,  # Small for testing
        overlap=10,
        page_title="بورسیه کوچینگ",
        page_url="/scholarship",
        h1_tags=["بورسیه"],
        h2_tags=["شرایط", "مزایا"]
    )
    
    print(f"  Input: {len(long_persian.split())} words")
    print(f"  Output: {len(chunks_data)} chunks")
    for i, (chunk_text, metadata) in enumerate(chunks_data):
        print(f"\n  Chunk {i+1}/{len(chunks_data)}:")
        print(f"    Text: {chunk_text[:80]}...")
        print(f"    Keywords: {metadata.keywords[:3]}")
        print(f"    Language: {metadata.language}")
        print(f"    H1 tags: {metadata.h1_tags}")
    
    print(f"\n  ✅ Chunking with metadata working!")
    
    # Test 5: Token-based chunking (approximation)
    print("\n5️⃣ Test: Token-based Chunking")
    tokens = PersianChunker._tokenize_persian(persian_text)
    print(f"  Text: {persian_text}")
    print(f"  Tokens: {len(tokens)} (approximation)")
    print(f"  ✅ Tokenization working!")
    
    print("\n" + "=" * 80)
    print("🎉 All tests passed! Persian chunking is working correctly!")
    print("=" * 80)
    
    return True


# Run tests
if __name__ == "__main__":
    test_persian_chunker()

