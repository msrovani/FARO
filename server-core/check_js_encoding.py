with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the script section
script_start = content.find('<script>')
script_end = content.find('</script>', script_start)
if script_start == -1 or script_end == -1:
    print("Script section not found")
else:
    script_content = content[script_start:script_end]
    lines = script_content.split('\n')
    
    print(f"Script section found, {len(lines)} lines")
    print("\nChecking for problematic characters:")
    
    for i, line in enumerate(lines[:100], start=1):
        # Check for non-ASCII characters
        if any(ord(c) > 127 for c in line):
            print(f"Line {i}: {repr(line[:100])}")
    
    # Check for problematic patterns
    print("\nChecking for problematic patterns:")
    patterns = [
        ("backtick inside backtick", "`.*`.*`"),
        ("unclosed string", "[\"'].*$"),
        ("unclosed comment", "/\\*.*$"),
    ]
    
    import re
    for pattern_name, pattern in patterns:
        matches = re.findall(pattern, script_content, re.MULTILINE)
        if matches:
            print(f"\n{pattern_name}: {len(matches)} matches")
