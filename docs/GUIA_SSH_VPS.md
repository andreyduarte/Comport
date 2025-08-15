# Guia de Sincronização com VPS via SSH

## 🎯 Configuração para seu Ambiente

### Seu Acesso Atual
```bash
ssh root@ip.do.server
# (solicita senha)
```

### Scripts Configurados
Os scripts foram ajustados para funcionar com:
- **Usuário**: `root` (padrão)
- **Autenticação**: Senha SSH
- **Método**: Comando SSH direto

## 🚀 Como Usar

### Método 1: Script Simples (Recomendado)
```bash
# Sincronizar com IP específico
python sync_simple.py 192.168.1.100

# Ou executar e digitar IP quando solicitado
python sync_simple.py
```

### Método 2: Script Completo
```bash
# Sincronizar especificando IP
python backup_restore.py sync 192.168.1.100

# Ou com usuário específico
python backup_restore.py sync 192.168.1.100 root
```

## 📋 Processo Automático

### O que acontece:
1. **Conecta na VPS** via SSH (solicita senha)
2. **Executa backup** no container PostgreSQL da VPS
3. **Baixa dados** diretamente para sua máquina
4. **Pergunta se quer restaurar** no ambiente local
5. **Para aplicação local** temporariamente
6. **Restaura dados** no PostgreSQL local
7. **Reinicia aplicação** local

### Comandos Executados:
```bash
# Na VPS (via SSH)
docker exec quiz_db pg_dump -U quiz_user -d quiz --no-owner --no-privileges

# Localmente (se escolher restaurar)
docker-compose down
docker-compose up -d db
docker exec -i quiz_db psql -U quiz_user -d quiz < backup.sql
docker-compose up -d
```

## 🔧 Configurações Necessárias

### Na VPS (Verificar se está OK)
```bash
# Conectar na VPS
ssh root@seu.ip.aqui

# Verificar se containers estão rodando
docker ps

# Deve mostrar containers: quiz_db e psicoquiz
```

### No Ambiente Local
```bash
# Verificar se Docker está rodando
docker ps

# Verificar se projeto está no diretório correto
ls docker-compose.yml
```

## 🛠️ Troubleshooting

### Erro de Conexão SSH
```bash
# Testar conexão manual
ssh root@seu.ip.aqui "echo 'Conexão OK'"
```

### Erro no Container da VPS
```bash
# Conectar na VPS e verificar
ssh root@seu.ip.aqui
docker ps
docker-compose logs
```

### Erro no Backup Local
```bash
# Verificar se containers locais estão OK
docker-compose ps
docker-compose logs db
```

### Arquivo de Backup Vazio
- Verifique se o container `quiz_db` está rodando na VPS
- Verifique se há dados no banco da VPS
- Teste o comando manualmente na VPS

## 📝 Exemplo Completo

```bash
# 1. Executar sincronização
python sync_simple.py

# 2. Digitar IP quando solicitado
# Digite o IP do servidor: 192.168.1.100

# 3. Digitar senha SSH quando solicitado
# root@192.168.1.100's password: [sua_senha]

# 4. Aguardar download
# ✅ Backup baixado: vps_backup_20241201_143022.sql

# 5. Confirmar restauração
# 🔄 Restaurar dados no ambiente local? (y/N): y

# 6. Aguardar processo
# ✅ Dados restaurados com sucesso!
# 🚀 Aplicação reiniciada!
```

## ⚡ Comandos Rápidos

### Sincronização Express
```bash
# Uma linha só (substitua o IP)
python sync_simple.py 192.168.1.100 && echo "Sincronização concluída!"
```

### Backup Manual da VPS
```bash
# Apenas baixar sem restaurar
ssh root@192.168.1.100 "docker exec quiz_db pg_dump -U quiz_user -d quiz" > backup_manual.sql
```

### Restaurar Backup Específico
```bash
# Restaurar arquivo específico
python backup_restore.py restore backup_manual.sql
```

---

**Próximo passo**: Testar a sincronização com `python sync_simple.py SEU_IP_AQUI`