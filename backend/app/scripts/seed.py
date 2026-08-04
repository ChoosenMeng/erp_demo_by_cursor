"""Run: python -m app.scripts.seed  (from backend/, conda env active)."""

from app.db.session import SessionLocal
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME, run_seed


def main() -> None:
    """Execute idempotent M1 seed and print a short summary."""
    db = SessionLocal()
    try:
        result = run_seed(db)
        print("Seed completed.")
        print(f"  company: {result['company_code']} (id={result['company_id']})")
        print(f"  admin:   {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print(f"  roles:   {', '.join(result['roles'])}")
        print(f"  perms:   {', '.join(result['permissions'])}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
