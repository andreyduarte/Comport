# Sistema de Migrações

## Configuração Automática
O sistema está configurado para executar migrações automaticamente durante o deploy via Docker.

## Comandos Manuais

### Inicializar migrações (apenas primeira vez)
```bash
python migrate.py init
```

### Criar nova migração após mudanças no modelo
```bash
python migrate.py create "Descrição da mudança"
```

### Aplicar migrações pendentes
```bash
python migrate.py apply
```

### Desfazer última migração
```bash
python migrate.py rollback
```

## Deploy Automatizado
```bash
./deploy.sh
```

## Fluxo de Desenvolvimento

1. **Modificar modelos** em `models.py`
2. **Criar migração**: `python migrate.py create "Nova coluna X"`
3. **Testar localmente**: `python migrate.py apply`
4. **Deploy**: `./deploy.sh` (aplica migrações automaticamente)

## Vantagens
- ✅ Zero downtime durante atualizações
- ✅ Rollback automático em caso de erro
- ✅ Backup automático antes do deploy
- ✅ Versionamento das mudanças no banco