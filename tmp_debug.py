from pathlib import Path
text = Path('templates/core/register.html').read_text(encoding='utf-8')
start = text.index('        <section class="adventurer-step" data-step="3">')
end = text.index('        <section class="adventurer-step" data-step="4">')
print(text[start:end])
