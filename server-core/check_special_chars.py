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
    print("\nChecking for special characters in first 50 lines of script:")
    
    for i, line in enumerate(lines[:50], start=1):
        # Check for non-ASCII characters
        if any(ord(c) > 127 for c in line):
            print(f"Line {i}: {repr(line[:80])}")
