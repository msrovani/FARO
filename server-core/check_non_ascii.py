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
    print("\nChecking for non-ASCII characters:")
    
    for i, line in enumerate(lines, start=1):
        # Check for non-ASCII characters
        non_ascii_chars = [c for c in line if ord(c) > 127]
        if non_ascii_chars:
            print(f"Line {i}: {len(non_ascii_chars)} non-ASCII chars: {repr(line[:100])}")
            for char in non_ascii_chars[:5]:
                print(f"  '{char}' (U+{ord(char):04X})")
