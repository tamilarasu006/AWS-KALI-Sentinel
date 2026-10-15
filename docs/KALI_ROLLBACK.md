# KALI Rollback Procedure

## Application Rollback
- Revert Docker container tags to the previous valid semantic version.
- `docker stop kali-api && docker run -d kali-api:v1.0.0`

## Database Rollback
- NEVER blindly run `alembic downgrade`.
- Restoring from the previous daily `pg_restore` checkpoint is preferred for destructive schema corruptions.

## Model Rollback
- Ensure model configurations reference explicit version tags (e.g., `kali-mini-tool:v1.0.0`).
