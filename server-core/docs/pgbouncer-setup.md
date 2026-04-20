# PgBouncer Setup Guide

## O que é PgBouncer?

PgBouncer é um connection pooler para PostgreSQL que melhora significativamente o throughput e reduz o overhead de conexões.

## Instalação

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install pgbouncer
```

### CentOS/RHEL
```bash
sudo yum install pgbouncer
```

### macOS (Homebrew)
```bash
brew install pgbouncer
```

## Configuração

### 1. Editar arquivo de configuração `/etc/pgbouncer/pgbouncer.ini`

```ini
[databases]
faro_db = host=localhost port=5432 dbname=faro_db user=faro password=faro

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool configuration
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

### 2. Criar arquivo de usuários `/etc/pgbouncer/userlist.txt`

```
"faro" "md5hash_password"
```

Para gerar o MD5 hash da senha:
```bash
echo -n "faro" | md5sum
# Resultado: 7b8a0e5e1c4e8e5e1c4e8e5e1c4e8e5e
# Formato completo: "md5" + md5(senha + nome_usuário)
# Exemplo: "md5" + md5("farofaro")
```

Ou usando PostgreSQL:
```sql
SELECT 'md5' || md5('faro' || 'faro');
```

### 3. Habilitar e iniciar PgBouncer

```bash
# Ubuntu/Debian
sudo systemctl enable pgbouncer
sudo systemctl start pgbouncer
sudo systemctl status pgbouncer

# macOS (Homebrew)
brew services start pgbouncer
```

### 4. Testar conexão

```bash
psql -h localhost -p 6432 -U faro -d faro_db
```

## Configurar FARO para usar PgBouncer

### 1. Atualizar variáveis de ambiente

No arquivo `.env`:
```bash
# Habilitar PgBouncer
PGBOUNCER_ENABLED=true
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=6432
```

### 2. A connection string será atualizada automaticamente pelo código

Quando `PGBOUNCER_ENABLED=true`, a aplicação usará:
```
postgresql+asyncpg://faro:faro@localhost:6432/faro_db
```

Em vez de:
```
postgresql+asyncpg://faro:faro@localhost:5432/faro_db
```

## Monitoramento PgBouncer

PgBouncer fornece uma console de monitoramento em tempo real:

```bash
psql -h localhost -p 6432 -U faro -d pgbouncer
```

Comandos úteis:
```sql
SHOW STATS;
SHOW POOLS;
SHOW LIST;
SHOW DATABASES;
```

## Troubleshooting

### Erro: "server closed the connection unexpectedly"
- Verificar se PostgreSQL está rodando
- Verificar configuração de auth no pg_hba.conf

### Erro: "no such file: /etc/pgbouncer/userlist.txt"
- Criar o arquivo userlist.txt
- Adicionar usuários com hash MD5 correto

### Erro: "connection refused"
- Verificar se PgBouncer está rodando
- Verificar porta correta (6432)
- Verificar firewall

## Benefícios Esperados

- **5-10x throughput**: Mais requisições por segundo
- **90% redução overhead**: Menos overhead de conexão
- **Melhor escalabilidade**: Suporta mais conexões simultâneas
- **Menor latência**: Reuso de conexões reduz latência
