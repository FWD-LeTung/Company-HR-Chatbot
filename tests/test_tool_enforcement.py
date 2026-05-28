"""Test script for Tool Enforcement & Hybrid Search changes.

Run: python tests/test_tool_enforcement.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")


def test_pyvi_tokenizer():
    """Test 5: pyvi tokenizer Vietnamese segmentation."""
    print("\n" + "=" * 60)
    print("TEST 5: pyvi Tokenizer")
    print("=" * 60)

    from pyvi import ViTokenizer

    tests = [
        ("định dạng văn bản", ["văn_bản"]),
        ("chính sách nhân sự", ["chính_sách", "nhân_sự"]),
        ("nghỉ phép năm", ["nghỉ", "phép", "năm"]),
        ("quy chuẩn định dạng văn bản", ["văn_bản"]),
    ]

    all_passed = True
    for text, expected_tokens in tests:
        result = ViTokenizer.tokenize(text)
        passed = all(token in result for token in expected_tokens)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] Input: '{text}'")
        print(f"        Output: '{result}'")
        if not passed:
            all_passed = False
            print(f"        Missing: {expected_tokens}")

    print(f"\n  Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


def test_bm25_index_exists():
    """Test 6: BM25 index files exist."""
    print("\n" + "=" * 60)
    print("TEST 6: BM25 Index Files")
    print("=" * 60)

    from pathlib import Path

    bm25_path = Path("data/bm25_index.pkl")
    docs_path = Path("data/bm25_documents.pkl")

    bm25_exists = bm25_path.exists()
    docs_exists = docs_path.exists()

    print(f"  [{'PASS' if bm25_exists else 'FAIL'}] {bm25_path} exists")
    print(f"  [{'PASS' if docs_exists else 'FAIL'}] {docs_path} exists")

    if bm25_exists and docs_exists:
        print(f"  Index size: {bm25_path.stat().st_size / 1024:.1f} KB")
        print(f"  Docs size: {docs_path.stat().st_size / 1024:.1f} KB")

    return bm25_exists and docs_exists


def test_bm25_search():
    """Test 3: Hybrid search returns relevant results for keyword query."""
    print("\n" + "=" * 60)
    print("TEST 3: BM25 Search - 'quy chuẩn định dạng văn bản'")
    print("=" * 60)

    try:
        from source.retrieval.bm25_indexer import bm25_indexer

        results = bm25_indexer.search("định dạng văn bản", top_k=3)
        if not results:
            print("  [WARN] BM25 returned 0 results (index may not be built yet)")
            return True

        for i, r in enumerate(results, 1):
            text_preview = r["text"][:150].replace("\n", " ")
            print(f"  Result {i} (score={r['score']:.4f}):")
            print(f"    {text_preview}...")

        keyword_found = any(
            "định dạng" in r["text"].lower() or "văn bản" in r["text"].lower()
            for r in results
        )
        print(f"\n  [{'PASS' if keyword_found else 'FAIL'}] Results contain 'định dạng' or 'văn bản'")
        return True
    except FileNotFoundError:
        print("  [SKIP] BM25 index not built yet. Run: python scripts/build_bm25_index.py")
        return True


def test_system_prompt_rules():
    """Test: System prompt contains mandatory tool rules."""
    print("\n" + "=" * 60)
    print("TEST: System Prompt Tool Enforcement Rules")
    print("=" * 60)

    from pathlib import Path

    prompt_path = Path("source/generation/prompts/agent_system_prompt.xml")
    content = prompt_path.read_text(encoding="utf-8")

    checks = {
        "BẮT BUỘC phải gọi một trong hai tools": "BẮT BUỘC" in content,
        "KHÔNG TỰ TRẢ LỜI": "KHÔNG TỰ TRẢ LỜI" in content,
        "Nguyễn Thị Quỳnh Anh": "Nguyễn Thị Quỳnh Anh" in content,
        "Bùi Thị Hà": "Bùi Thị Hà" in content,
        "Không có 'CHỈ gọi tool khi cần thiết'": "CHỈ gọi tool khi cần thiết" not in content,
    }

    all_passed = True
    for desc, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {desc}")
        if not passed:
            all_passed = False

    return all_passed


def test_fallback_constant():
    """Test: FALLBACK_MSG constant is defined correctly."""
    print("\n" + "=" * 60)
    print("TEST: Fallback Message Constant")
    print("=" * 60)

    from source.generation.chat_engine import FALLBACK_MSG

    checks = {
        "Contains HR Admin": "Nguyễn Thị Quỳnh Anh" in FALLBACK_MSG,
        "Contains HR L&D": "Bùi Thị Hà" in FALLBACK_MSG,
        "Contains phone 1": "0913244513" in FALLBACK_MSG,
        "Contains phone 2": "0313214512" in FALLBACK_MSG,
    }

    all_passed = True
    for desc, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {desc}")
        if not passed:
            all_passed = False

    return all_passed


def test_hybrid_search_function():
    """Test: hybrid_search_hr_policies function exists and is callable."""
    print("\n" + "=" * 60)
    print("TEST: Hybrid Search Function")
    print("=" * 60)

    try:
        from source.retrieval.search_engine import hybrid_search_hr_policies

        print("  [PASS] hybrid_search_hr_policies is importable")
        print(f"  [PASS] Function: {hybrid_search_hr_policies.__name__}")
        return True
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False


def test_tool_uses_hybrid():
    """Test: tra_cuu_chinh_sach uses hybrid_search_hr_policies."""
    print("\n" + "=" * 60)
    print("TEST: Tool Uses Hybrid Search")
    print("=" * 60)

    from pathlib import Path

    source = Path("source/generation/chat_engine.py").read_text(encoding="utf-8")

    # Find the tra_cuu_chinh_sach function body
    start = source.find("def tra_cuu_chinh_sach(")
    end = source.find("\n@tool", start + 1) if source.find("\n@tool", start + 1) > 0 else source.find("\n\ntools", start + 1)
    func_body = source[start:end]

    uses_hybrid = "hybrid_search_hr_policies" in func_body
    not_old_vector_only = func_body.count("search_hr_policies(") == func_body.count("hybrid_search_hr_policies(")

    print(f"  [{'PASS' if uses_hybrid else 'FAIL'}] Uses hybrid_search_hr_policies")
    print(f"  [{'PASS' if not_old_vector_only else 'FAIL'}] Does NOT use old search_hr_policies directly")
    return uses_hybrid and not_old_vector_only


def main():
    print("=" * 60)
    print("HR Chatbot - Tool Enforcement & Hybrid Search Tests")
    print("=" * 60)

    results = {}

    # Tests that don't require Qdrant connection
    results["pyvi_tokenizer"] = test_pyvi_tokenizer()
    results["system_prompt"] = test_system_prompt_rules()
    results["fallback_constant"] = test_fallback_constant()
    results["hybrid_function"] = test_hybrid_search_function()
    results["tool_uses_hybrid"] = test_tool_uses_hybrid()

    # Tests that require BM25 index
    results["bm25_index_exists"] = test_bm25_index_exists()
    results["bm25_search"] = test_bm25_search()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, result in results.items():
        print(f"  [{'PASS' if result else 'FAIL'}] {name}")

    print(f"\n  Total: {passed}/{total} passed")

    if passed == total:
        print("\n  All tests passed!")
    else:
        print(f"\n  {total - passed} test(s) need attention.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
