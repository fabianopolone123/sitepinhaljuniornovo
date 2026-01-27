from pathlib import Path
text = Path('DEPLOY_FLOW.md').read_text(encoding='latin-1')
start = text.index('11. SCRIPT DE DEPLOY PERSONALIZADO')
print(repr(text[start:]))
