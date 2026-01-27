========================================
FLUXO DE DEPLOY – PINHALJUNIOR
========================================

Este arquivo descreve o processo oficial de deploy do projeto Django  sitepinhaljuniornovo, do PC local até o VPS em produção.

========================================
1. VISÃO GERAL DO FLUXO
========================================

Fluxo padrão de atualização:

PC LOCAL
  +-- git add / commit / push
        +-- GitHub
              +-- VPS
                    +-- git pull
                          +-- ajustes Django
                                +-- restart Gunicorn

NUNCA editar arquivos do projeto diretamente no VPS, apenas via Git.

========================================
2. DEPLOY NO PC LOCAL (DESENVOLVIMENTO)
========================================

Entrar na pasta do projeto no computador local.

Comandos padrão:

git status
git add .
git commit -m descrição da alteração
git push origin main

Verificação antes de subir:

git status
git diff
git diff --staged

========================================
3. DEPLOY NO VPS (PRODUÇÃO)
========================================

Entrar no servidor via SSH:

ssh root@145.223.93.162

Ir para a pasta do projeto:

cd /var/www/sitepinhaljuniornovo

Atualizar o código:

git pull

========================================
4. AÇÕES PÓS-GIT PULL (DEPENDE DO QUE MUDOU)
========================================

----------------------------------------
4.1 Alterações em dependências Python
----------------------------------------

Se houve mudança no requirements.txt:

source venv/bin/activate
pip install -r requirements.txt

----------------------------------------
4.2 Alterações em models / banco de dados
----------------------------------------

Se houve mudança em models ou migrations:

source venv/bin/activate
python manage.py migrate

----------------------------------------
4.3 Alterações em arquivos estáticos
----------------------------------------

Se houve mudança em CSS, JS ou imagens:

source venv/bin/activate
python manage.py collectstatic --noinput

----------------------------------------
4.4 Templates HTML
----------------------------------------

Normalmente NÃO precisa collectstatic.
Apenas reiniciar o Gunicorn.

========================================
5. REINICIAR O APLICATIVO
========================================

Após qualquer alteração de código:

systemctl restart pinhaljunior

Verificar status:

systemctl status pinhaljunior --no-pager -l

========================================
6. O QUE NÃO FAZER
========================================

? NÃO editar arquivos do projeto direto no VPS  
? NÃO criar arquivos locais no servidor sem commitar  
? NÃO usar git pull se houver arquivos modificados no VPS  

Isso causa erro:
Your local changes would be overwritten by merge

========================================
7. ARQUIVOS QUE NÃO DEVEM IR PARA O GIT
========================================

Arquivos e pastas fora do versionamento:

- db.sqlite3 (opcional, depende do fluxo)
- venv/
- staticfiles/
- .env (se existir)
- arquivos de log

========================================
8. COMANDOS DE VERIFICAÇÃO RÁPIDA
========================================

Ver status do Gunicorn:
systemctl status pinhaljunior

Ver se o Django responde localmente:
curl -I http://127.0.0.1:8000

Ver se o site responde externamente:
curl -I https://pinhaljunior.com.br

========================================
9. FLUXO RESUMIDO (COLA E USA)
========================================

PC LOCAL:
git add .
git commit -m update
git push origin main

VPS:
cd /var/www/sitepinhaljuniornovo
git pull
source venv/bin/activate
python manage.py migrate        # se necessário
python manage.py collectstatic --noinput  # se necessário
systemctl restart pinhaljunior

========================================
10. STATUS FINAL ESPERADO
========================================

- Código atualizado no VPS
- Gunicorn rodando
- Django respondendo
- Site disponível via HTTPS
- OpenLiteSpeed sem necessidade de restart

========================================
FIM DO ARQUIVO
========================================
========================================
11. SCRIPT DE DEPLOY PERSONALIZADO
========================================

Há um helper script no VPS para simplificar o deploy completo.

No VPS (após o git pull e os passos de migração/collectstatic):

cd /var/www/sitepinhaljuniornovo
./deploy_pinhaljunior.sh

Esse script já define o ambiente, instala dependências, aplica migrations e reinicia o Gunicorn de forma segura.
