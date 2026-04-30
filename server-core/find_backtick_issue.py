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
    print("\nChecking for backtick issues:")
    
    in_backtick = False
    backtick_start_line = None
    
    for i, line in enumerate(lines, start=1):
        backtick_count = line.count('`')
        
        if backtick_count % 2 == 1:
            if not in_backtick:
                in_backtick = True
                backtick_start_line = i
                print(f"Line {i}: Backtick opened: {repr(line[:80])}")
            else:
                in_backtick = False
                print(f"Line {i}: Backtick closed: {repr(line[:80])}")
                backtick_start_line = None
    
    if in_backtick:
        print(f"\nERROR: Unclosed backtick starting at line {backtick_start_line}")
