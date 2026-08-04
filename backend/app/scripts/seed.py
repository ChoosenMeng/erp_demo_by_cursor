"""Run: python -m app.scripts.seed

From backend/, with conda env cursor-erp-demo active.
Seeds orgs/roles/users + multi-company master data + currencies.
"""

from app.db.session import SessionLocal
from app.modules.demo.seed import run_demo_seed
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME, DEMO_PASSWORD, run_seed


def main() -> None:
    """Execute org + demo seed and print a short summary."""
    db = SessionLocal()
    try:
        org = run_seed(db)
        demo = run_demo_seed(db, with_second_company=True)
        print("Seed completed.")
        print(f"  active:    {', '.join(org['companies'])}")
        print(f"  inactive:  {', '.join(org.get('inactive_companies', []))}")
        print(f"  admin:     {ADMIN_USERNAME} / {ADMIN_PASSWORD}  (USCO+EUCO, default USCO)")
        print(f"  demo pwd:  {DEMO_PASSWORD}")
        print(f"  users:     {', '.join(org['demo_users'])}")
        print(f"  roles:     {', '.join(org['roles'])}")
        print(f"  masters:   {[m['company_code'] + '/' + m['base_currency'] for m in demo['masters']]}")
        print(f"  materials: {demo.get('material_counts')}")
        print(f"  txs:       {[{'company': t.get('company_code'), 'skipped': t.get('skipped')} for t in demo.get('transactions', [])]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
