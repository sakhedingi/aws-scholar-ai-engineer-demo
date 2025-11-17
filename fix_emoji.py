#!/usr/bin/env python3
import os
import re

os.chdir(os.path.dirname(__file__))

files = [
    'bedrock_app/optimized_rag.py',
    'bedrock_app/vector_store_manager.py',
    'bedrock_app/prompt_cache.py',
    'bedrock_app/semantic_search.py',
    'app.py'
]

for filepath in files:
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all non-ASCII characters in print statements
    # This regex finds print statements and removes emoji
    def clean_print(match):
        statement = match.group(0)
        # Remove all characters outside ASCII range
        cleaned = ''.join(c if ord(c) < 128 else '' for c in statement)
        return cleaned
    
    # Find and clean all print( statements
    original = content
    content = re.sub(r'print\([^)]*\)', clean_print, content)
    
    # Also handle multi-line print statements
    content = re.sub(r'print\(f"[^"]*"[^)]*\)', clean_print, content)
    
    # Brute force: replace common emoji patterns
    emoji_chars = [c for c in content if ord(c) > 127]
    for emoji in set(emoji_chars):
        content = content.replace(emoji, '')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✓ Fixed: {filepath}')
    else:
        print(f'✓ Already clean: {filepath}')

print('\nDone!')
