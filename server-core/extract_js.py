with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the script section
script_start = content.find('<script>')
script_end = content.find('</script>', script_start)
if script_start == -1 or script_end == -1:
    print("Script section not found")
else:
    script_content = content[script_start + len('<script>'):script_end]
    
    # Save to file
    with open('test_script.js', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"Script extracted to test_script.js ({len(script_content)} chars)")
