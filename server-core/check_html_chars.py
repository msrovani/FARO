with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the HTML section
html_start = content.find('DASHBOARD_HTML = """')
html_end = content.find('"""', html_start + 20)
if html_start == -1 or html_end == -1:
    print("HTML section not found")
else:
    html_content = content[html_start + 20:html_end]
    
    # Check for problematic characters in HTML
    print("Checking for problematic characters in HTML...")
    
    for i, line in enumerate(html_content.split('\n')[:100], start=1):
        # Check for problematic patterns
        if '&quot;' in line and 'onclick' in line:
            print(f"Line {i}: &quot; in onclick: {repr(line[:100])}")
