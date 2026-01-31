import pathlib
text = pathlib.Path('templates/core/register.html').read_text(encoding='utf-8')
pos = text.find('Endere')
print(text[pos-80:pos+400])
