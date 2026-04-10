# Migrations

This project uses Alembic-style SQLAlchemy metadata migrations. For this delivery, schema bootstrap is handled by `Base.metadata.create_all` on startup for zero-touch local Windows setup.

For production, run:

```bash
alembic revision --autogenerate -m "..."
alembic upgrade head
```
