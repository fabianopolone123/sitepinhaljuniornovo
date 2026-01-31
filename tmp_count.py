from pathlib import Path
text = Path('templates/core/register.html').read_text(encoding='utf-8')
start = 0
while True:
    idx = text.find('adventurer-count-control', start)
    if idx == -1:
        break
    line = text.count('\n', 0, idx) + 1
    print('line', line)
    start = idx + 1
