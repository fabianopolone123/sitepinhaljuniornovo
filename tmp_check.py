from pathlib import Path
text = Path('core/views.py').read_text(encoding='utf-8')
old = '''        if User.objects.filter(username=responsible_username).exists():
            field_errors[" responsavel_username\] = \Nome de usuário indisponível.\\n'''
print(old in text)
