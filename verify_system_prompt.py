#!/usr/bin/env python3
"""
Verify system prompt integration is working correctly.
Run this script to ensure all components are in place.
"""

import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a required file exists."""
    if Path(filepath).exists():
        print(f"[OK] {description}: {filepath}")
        return True
    else:
        print(f"[FAIL] {description} NOT FOUND: {filepath}")
        return False

def check_import(module_path, description):
    """Check if a Python module can be imported."""
    try:
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        print(f"[OK] {description}: {module_path}")
        return True
    except ImportError as e:
        print(f"[FAIL] {description} IMPORT FAILED: {module_path}")
        print(f"      Error: {e}")
        return False

def check_system_prompt_content():
    """Verify system prompt file has expected content."""
    prompt_file = Path(__file__).parent / "SYSTEM_PROMPT_NESD_QA.md"
    
    if not prompt_file.exists():
        print(f"[FAIL] System prompt file not found: {prompt_file}")
        return False
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            "Core Identity",
            "Domain Knowledge",
            "Gherkin Scripting Rules",
            "Response Guidelines",
            "Common Patterns"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"[WARN] System prompt missing sections: {missing_sections}")
            return False
        
        print(f"[OK] System prompt has all required sections ({len(content)} chars)")
        return True
    except Exception as e:
        print(f"[FAIL] Error reading system prompt: {e}")
        return False

def check_integration():
    """Verify integration in optimized_rag.py."""
    rag_file = Path(__file__).parent / "bedrock_app" / "optimized_rag.py"
    
    if not rag_file.exists():
        print(f"[FAIL] optimized_rag.py not found: {rag_file}")
        return False
    
    try:
        with open(rag_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_imports = ["from .system_prompt import load_system_prompt"]
        required_calls = ["system_prompt = load_system_prompt()"]
        
        all_found = True
        for imp in required_imports:
            if imp not in content:
                print(f"[FAIL] Integration missing: {imp}")
                all_found = False
        
        for call in required_calls:
            if call not in content:
                print(f"[FAIL] Integration missing: {call}")
                all_found = False
        
        if all_found:
            print(f"[OK] optimized_rag.py properly integrated with system prompt")
        
        return all_found
    except Exception as e:
        print(f"[FAIL] Error checking integration: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("NESD-QA System Prompt Verification")
    print("=" * 60)
    print()
    
    base_path = Path(__file__).parent
    
    checks = [
        # Files
        (lambda: check_file_exists(base_path / "SYSTEM_PROMPT_NESD_QA.md", "System Prompt File"), "File Check"),
        (lambda: check_file_exists(base_path / "bedrock_app" / "system_prompt.py", "System Prompt Module"), "File Check"),
        (lambda: check_file_exists(base_path / "SYSTEM_PROMPT_INTEGRATION_GUIDE.md", "Integration Guide"), "File Check"),
        (lambda: check_file_exists(base_path / "SYSTEM_PROMPT_BEST_PRACTICES.md", "Best Practices"), "File Check"),
        (lambda: check_file_exists(base_path / "SYSTEM_PROMPT_SUMMARY.md", "Summary"), "File Check"),
        
        # Content
        (lambda: check_system_prompt_content(), "Content Check"),
        
        # Integration
        (lambda: check_integration(), "Integration Check"),
    ]
    
    results = []
    current_section = None
    
    for check, section in checks:
        if section != current_section:
            if current_section is not None:
                print()
            print(f"\n{section}:")
            print("-" * 40)
            current_section = section
        
        result = check()
        results.append(result)
    
    print()
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"SUCCESS: All {total} checks passed!")
        print()
        print("Your NESD-QA system prompt is ready to use:")
        print("  1. Start: streamlit run app.py")
        print("  2. Enable RAG mode")
        print("  3. Ask: 'Write a prepaid data bundle test'")
        print("  4. Verify: Response includes complete Gherkin script")
        print()
        return 0
    else:
        print(f"WARNING: {passed}/{total} checks passed, {total-passed} issues found")
        print()
        print("Please check the failures above and refer to:")
        print("  - SYSTEM_PROMPT_INTEGRATION_GUIDE.md")
        print("  - SYSTEM_PROMPT_BEST_PRACTICES.md")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
