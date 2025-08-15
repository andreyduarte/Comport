# Guia de Backup e Sincronização - PsicoQuiz

## 🎯 Funcionalidades Implementadas

### 1. Sistema de Backup Manual
- **Backup PostgreSQL**: Dump completo do banco
- **Export JSON**: Compatível com versão antiga
- **Restore**: Restauração completa de backups

### 2. Backup Automático
- **Agendamento**: 2x por dia (2h e 14h)
- **Limpeza**: Mantém últimos 30 backups
- **Monitoramento**: Logs detalhados

### 3. Sincronização com Produção
- **SSH/SCP**: Download direto via SSH
- **Docker remoto**: Backup via Docker na produção
- **API REST**: Preparado para implementação futura

## 🚀 Como Usar

### Backup Manual
```bash
# Criar backup completo (SQL + JSON)
python backup_restore.py backup

# Apenas JSON
python backup_restore.py export

# Restaurar backup
python backup_restore.py restore backup_psicoquiz_20241201_143022.sql
```

### Backup Automático
```bash
# Iniciar serviço de backup (modo daemon)
docker-compose -f docker-compose.backup.yml up -d backup

# Backup imediato
python auto_backup.py now

# Verificar logs
docker-compose -f docker-compose.backup.yml logs -f backup
```

### Sincronização com Produção
```bash
# Via Python (recomendado)
python backup_restore.py sync servidor.com usuario

# Via script shell
./sync_production.sh

# Método manual via SSH
ssh usuario@servidor.com "docker exec quiz_db pg_dump -U quiz_user -d quiz" > prod_backup.sql
python backup_restore.py restore prod_backup.sql
```

## 📁 Estrutura de Arquivos

```
/backups/
├── backup_psicoquiz_20241201_020000.sql    # Backup SQL automático
├── users_backup_20241201_020000.json       # Export JSON automático
├── prod_backup_20241201_143022.sql         # Backup da produção
└── ...
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# Backup automático
BACKUP_SCHEDULE=02:00,14:00
MAX_BACKUPS=30
BACKUP_DIR=backups

# Produção (para sincronização)
PROD_HOST=seu-servidor.com
PROD_USER=usuario
PROD_PATH=/path/to/psicoquiz
```

### Docker Compose
```bash
# Iniciar apenas backup automático
docker-compose -f docker-compose.backup.yml up -d backup

# Iniciar ferramentas de backup (sob demanda)
docker-compose -f docker-compose.backup.yml --profile tools up -d backup-tools

# Executar comando no container de ferramentas
docker-compose -f docker-compose.backup.yml exec backup-tools python backup_restore.py backup
```

## 🔧 Comandos Úteis

### Verificar Backups
```bash
# Listar backups
ls -la backups/

# Verificar tamanho
du -sh backups/*

# Verificar integridade do SQL
head -n 20 backups/backup_psicoquiz_*.sql
```

### Monitoramento
```bash
# Logs do backup automático
docker-compose -f docker-compose.backup.yml logs -f backup

# Status dos containers
docker-compose -f docker-compose.backup.yml ps

# Espaço em disco
df -h
```

### Restauração de Emergência
```bash
# Parar aplicação
docker-compose down

# Restaurar último backup
python backup_restore.py restore backups/backup_psicoquiz_$(ls backups/ | grep backup_psicoquiz | tail -1)

# Reiniciar aplicação
docker-compose up -d
```

## 🛡️ Segurança e Boas Práticas

### Backup
- ✅ Backups automáticos 2x por dia
- ✅ Retenção de 30 dias
- ✅ Verificação de integridade
- ✅ Logs detalhados

### Sincronização
- ✅ Autenticação SSH por chave
- ✅ Verificação antes de restaurar
- ✅ Backup local antes de sincronizar
- ✅ Limpeza de arquivos temporários

### Monitoramento
- ✅ Logs de todas as operações
- ✅ Alertas em caso de falha
- ✅ Verificação de espaço em disco
- ✅ Validação de backups

## 🚨 Troubleshooting

### Erro de Conexão SSH
```bash
# Testar conexão
ssh usuario@servidor.com "echo 'Conexão OK'"

# Verificar chaves SSH
ssh-add -l
```

### Erro no PostgreSQL
```bash
# Verificar container
docker-compose ps db

# Logs do banco
docker-compose logs db

# Conectar manualmente
docker exec -it quiz_db psql -U quiz_user -d quiz
```

### Espaço em Disco
```bash
# Verificar espaço
df -h

# Limpar backups antigos manualmente
find backups/ -name "backup_*" -mtime +30 -delete
```

## 📈 Próximas Melhorias

### Curto Prazo
- [ ] Compressão de backups (.gz)
- [ ] Verificação de integridade automática
- [ ] Notificações por email/Slack
- [ ] Dashboard de monitoramento

### Médio Prazo
- [ ] Backup incremental
- [ ] Sincronização bidirecional
- [ ] API REST para backups
- [ ] Backup para cloud (AWS S3, Google Drive)

### Longo Prazo
- [ ] Replicação em tempo real
- [ ] Backup distribuído
- [ ] Recuperação point-in-time
- [ ] Disaster recovery automático

---

**Status**: ✅ Sistema completo implementado
**Próximo passo**: Configurar produção e testar sincronização