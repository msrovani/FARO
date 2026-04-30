import requests

response = requests.get('http://localhost:9002/dashboard')
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Content-Length: {len(response.text)}")
print(f"Encoding: {response.encoding}")

# Check if the response is complete
if len(response.text) > 0:
    # Check if the HTML is complete
    if response.text.endswith('</html>'):
        print("HTML appears to be complete")
    else:
        print("HTML appears to be incomplete")
        print(f"Last 100 chars: {repr(response.text[-100:])}")
    
    # Check for script tag
    if '<script>' in response.text and '</script>' in response.text:
        print("Script tag found and closed")
    else:
        print("Script tag not found or not closed")
