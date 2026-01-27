# VPS Deployment Details

Este arquivo documenta o ambiente atual do VPS que hospeda o projeto `sitepinhaljuniornovo`.

## 1. Informações gerais do servidor
- **Sistema**: Ubuntu Linux
- **Usuário principal**: root
- **IP público**: 145.223.93.162
- **Domínio(s)**: pinhaljunior.com.br / www.pinhaljunior.com.br

## 2. Estrutura de pastas
- **Raiz do projeto**: `/var/www/sitepinhaljuniornovo`
- **Arquivos principais**: `manage.py`, `requirements.txt`, `db.sqlite3`, `staticfiles/`, `.well-known/`, `venv/`
- **Permissões**:
  - Pasta do projeto: `chown root:www-data /var/www/sitepinhaljuniornovo` e `chmod 775`.
  - Banco de dados: `chown root:www-data /var/www/sitepinhaljuniornovo/db.sqlite3` e `chmod 664`.

## 3. Ambiente Python / Django
- **Virtualenv**: `/var/www/sitepinhaljuniornovo/venv`
  - Ativação: `source /var/www/sitepinhaljuniornovo/venv/bin/activate`
- **Python**: 3.12
- **Dependências principais**: Django 6.0.1, Gunicorn 24.1.1, Pillow, Requests
- **Instalação**: `pip install -r requirements.txt`
- **Banco de dados**: SQLite (`/var/www/sitepinhaljuniornovo/db.sqlite3`)
- **Migrations**: `python manage.py migrate`
- **Static files**: `python manage.py collectstatic --noinput` -> `/var/www/sitepinhaljuniornovo/staticfiles`
- **Superusuário**: `fabianopolone`

## 4. Serviço Gunicorn (systemd)
- **Service name**: `pinhaljunior.service`
- **Localização**: `/etc/systemd/system/pinhaljunior.service`
- **Configurações principais**:
  - User: root, Group: www-data
  - WorkingDirectory: `/var/www/sitepinhaljuniornovo`
  - Environment: `PATH` para virtualenv, `DJANGO_SETTINGS_MODULE=pinhaljunior.settings`
  - ExecStart: `/var/www/sitepinhaljuniornovo/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --access-logfile /var/log/pinhaljunior/access.log --error-logfile /var/log/pinhaljunior/error.log pinhaljunior.wsgi:application`
  - Logs: `/var/log/pinhaljunior/access.log` e `/var/log/pinhaljunior/error.log`
  - Restart: always com `RestartSec=3`
  - Serviço está ativo (porta 127.0.0.1:8000)

## 5. OpenLiteSpeed
- **Serviço**: `lshttpd` (portas 80/443)
- **Configuração**: `/usr/local/lsws/conf/httpd_config.conf`
- **Virtual Host**: `pinhaljunior`
  - Document root: `/var/www/sitepinhaljuniornovo/`
  - Django proxy: processador `django8000` enviando para `http://127.0.0.1:8000`
  - Contextos para `/static/` e `/.well-known/acme-challenge/`
  - Contexto `/` proxy para o `django8000`

## 6. Mapeamento de domínio (OLS)
- **Listeners** (`Default` e `Defaultssl`) mapeiam `pinhaljunior` para `pinhaljunior.com.br` e `www.pinhaljunior.com.br`
- **vhRoot**: `/var/www/sitepinhaljuniornovo/`

## 7. SSL / Let's Encrypt
- **Certificados**: para pinhaljunior.com.br e www.pinhaljunior.com.br
  - Cert: `/etc/letsencrypt/live/pinhaljunior.com.br/fullchain.pem`
  - Key: `/etc/letsencrypt/live/pinhaljunior.com.br/privkey.pem`
- **Configuração SSL**: listener `Defaultssl` usa esses arquivos

## 8. Renovação automática (certbot)
- **Timer**: `certbot.timer` roda duas vezes por dia
- **Arquivo de renovação**: `/etc/letsencrypt/renewal/pinhaljunior.com.br.conf`
- **Modo webroot**: `webroot_path` `/var/www/sitepinhaljuniornovo`
- **Mapeamento de domínio**: `pinhaljunior.com.br` e `www.pinhaljunior.com.br` apontam para o mesmo webroot
- **Teste**: `certbot renew --dry-run` (SUCESSO)

## 9. Hook de reload SSL
- **Arquivo**: `/etc/letsencrypt/renewal-hooks/deploy/reload-lsws.sh`
  - Conteúdo: `systemctl reload lshttpd 2>/dev/null || systemctl restart lshttpd`
  - Permissão: `chmod +x`

## 10. Status atual (resumo)
- Gunicorn: OK
- Django: OK
- SQLite: OK
- Static files: OK
- OpenLiteSpeed: OK
- HTTP (80) / HTTPS (443): OK
- SSL válido: OK
- Renovação automática: OK

Sistema em produção e funcional.
