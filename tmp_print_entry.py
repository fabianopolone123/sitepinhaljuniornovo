# -*- coding: latin-1 -*-
from pathlib import Path
text = Path('SYSTEM_ACTIVITY.md').read_text(encoding='latin-1')
lines = text.splitlines()
for idx, line in enumerate(lines):
    if 'Refaz cadastro' in line:
        for i in range(idx, idx+6):
            print(i, repr(lines[i]))
        break
