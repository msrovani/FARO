with open('analytics_dashboard/app.py', 'rb') as f:
    raw_content = f.read()
    
# Check for BOM
if raw_content.startswith(b'\xef\xbb\xbf'):
    print("File has UTF-8 BOM")
elif raw_content.startswith(b'\xff\xfe'):
    print("File has UTF-16 LE BOM")
elif raw_content.startswith(b'\xfe\xff'):
    print("File has UTF-16 BE BOM")
else:
    print("No BOM detected")

# Try to decode as UTF-8
try:
    content = raw_content.decode('utf-8')
    print("File is valid UTF-8")
except UnicodeDecodeError as e:
    print(f"UTF-8 decode error: {e}")
    
# Check for null bytes
null_count = raw_content.count(b'\x00')
if null_count > 0:
    print(f"Found {null_count} null bytes")
