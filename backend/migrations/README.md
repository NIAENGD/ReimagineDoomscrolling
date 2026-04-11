# Migrations

This project now includes a concrete Alembic environment and initial revision under `backend/alembic/`.
For local bootstrap convenience, the app still keeps `Base.metadata.create_all` on startup, but schema evolution should use Alembic revisions.

For production, run:

```bash
cd backend
alembic -c alembic.ini upgrade head
```
