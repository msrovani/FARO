with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the HTML section
html_start = content.find('DASHBOARD_HTML = """')
html_end = content.find('"""', html_start + 20)
if html_start == -1 or html_end == -1:
    print("HTML section not found")
else:
    html_content = content[html_start + 20:html_end]
    
    # Check for unclosed tags
    print("Checking for unclosed HTML tags...")
    
    from collections import defaultdict
    tags = []
    tag_stack = []
    
    for i, char in enumerate(html_content):
        if char == '<':
            # Find the tag
            tag_end = html_content.find('>', i)
            if tag_end == -1:
                continue
            
            tag_content = html_content[i+1:tag_end]
            
            # Skip comments and DOCTYPE
            if tag_content.startswith('!') or tag_content.startswith('?'):
                continue
            
            # Extract tag name
            tag_name = tag_content.split()[0].replace('/', '')
            
            # Check if it's a closing tag
            if tag_content.startswith('/'):
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
            # Check if it's a self-closing tag
            elif tag_content.endswith('/') or tag_name in ['br', 'hr', 'img', 'input', 'meta', 'link']:
                pass
            else:
                tag_stack.append(tag_name)
    
    if tag_stack:
        print(f"Unclosed tags: {tag_stack}")
    else:
        print("All tags are properly closed")
