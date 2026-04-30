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
    print("\nChecking for unclosed strings:")
    
    in_string = False
    string_char = None
    for i, line in enumerate(lines, start=1):
        j = 0
        while j < len(line):
            char = line[j]
            
            # Check for string start/end
            if char in ['"', "'", '`'] and (j == 0 or line[j-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            j += 1
        
        if in_string:
            print(f"Line {i}: Unclosed string ({string_char}): {repr(line[:80])}")
