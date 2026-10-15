# KALI Database Backup Strategy

## Backup Procedure
Automated PostgreSQL snapshots using `pg_dump`.
```bash
pg_dump -U postgres -h localhost -d kali_db -F c -f /backups/kali_db_backup_$(date +%F).dump
```

## Retention Policy
- Daily backups kept for 7 days.
- Weekly backups kept for 4 weeks.

## Restore Procedure (Disaster Recovery Test Required)
```bash
pg_restore -U postgres -h localhost -d kali_db -1 /backups/kali_db_backup_date.dump
```
