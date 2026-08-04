"""Run: python -m app.scripts.seed [--with-second-company]

From backend/, with conda env cursor-erp-demo active.
"""

import argparse

from app.db.session import SessionLocal
from app.modules.demo.seed import run_demo_seed
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME, run_seed


def main() -> None:
    """Execute org + demo seed and print a short summary."""
    parser = argparse.ArgumentParser(description="Seed Cursor ERP Demo data")
    parser.add_argument(
        "--with-second-company",
        action="store_true",
        help="Also seed SECOND company and link admin (multi-company smoke)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        org = run_seed(db)
        # Org seed commits; open a fresh transaction for demo data
        demo = run_demo_seed(db, with_second_company=args.with_second_company)
        print("Seed completed.")
        print(f"  company: {org['company_code']} (id={org['company_id']})")
        print(f"  admin:   {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print(f"  roles:   {', '.join(org['roles'])}")
        print(f"  perms:   {', '.join(org['permissions'])}")
        print(
            "  master:  "
            f"customer={demo['master']['customer_id']}, "
            f"supplier={demo['master']['supplier_id']}, "
            f"warehouse={demo['master']['warehouse_id']}, "
            f"materials={demo['master']['material_ids']}"
        )
        if demo.get("second_company_id"):
            print(
                f"  second:  {demo['second_company_code']} "
                f"(id={demo['second_company_id']})"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
