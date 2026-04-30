with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the HTML section
html_start = content.find('DASHBOARD_HTML = """')
html_end = content.find('"""', html_start + 20)
if html_start == -1 or html_end == -1:
    print("HTML section not found")
else:
    html_content = content[html_start + 20:html_end]
    
    # Check if the script tag is properly closed
    script_start = html_content.find('<script>')
    script_end = html_content.find('</script>', script_start)
    
    if script_start == -1 or script_end == -1:
        print("Script tag not found or not closed")
    else:
        print(f"Script tag found at position {script_start} to {script_end}")
        print(f"Script content length: {script_end - script_start}")
        
        # Check if there are any issues with the script tag
        script_section = html_content[script_start:script_end + 9]
        print(f"Script section first 200 chars: {repr(script_section[:200])}")
        print(f"Script section last 200 chars: {repr(script_section[-200:])}")
