import re

with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the script section
script_start = content.find('<script>')
script_end = content.find('</script>', script_start)
if script_start == -1 or script_end == -1:
    print("Script section not found")
else:
    script_content = content[script_start:script_end]
    print(f"Script section found, length: {len(script_content)}")
    
    # Check for problematic patterns
    patterns = [
        (r"onclick='[^']*'", "Single quotes in onclick"),
        (r"onclick=\"[^\"]*'[^']*\"", "Mixed quotes in onclick"),
        (r"exportAudit\('[^']+'\)", "exportAudit with single quotes"),
        (r"exportAlertHistory\('[^']+'\)", "exportAlertHistory with single quotes"),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, script_content)
        if matches:
            print(f"\n{description}: {len(matches)} matches")
            for match in matches[:5]:
                print(f"  {match}")
