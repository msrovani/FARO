with open('analytics_dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    print(f'File length: {len(content)}')
    print(f'Total lines: {len(lines)}')
    print('\nLines 1250-1260:')
    for i, line in enumerate(lines[1249:1260], start=1250):
        print(f'{i}: {repr(line[:100])}')
