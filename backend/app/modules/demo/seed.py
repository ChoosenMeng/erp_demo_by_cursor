"""Idempotent demo master data and optional second company (M5)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.master.models import Customer, Material, Supplier, Warehouse
from app.modules.master.services import ensure_currency_cny
from app.modules.org.models import Company, User, UserCompany


def _get_or_create_customer(db: Session, company_id: int, code: str, name: str) -> Customer:
    row = db.scalar(
        select(Customer).where(Customer.company_id == company_id, Customer.code == code)
    )
    if row:
        return row
    row = Customer(
        company_id=company_id,
        code=code,
        name=name,
        contact_name="演示联系人",
        contact_phone="13800000000",
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_supplier(db: Session, company_id: int, code: str, name: str) -> Supplier:
    row = db.scalar(
        select(Supplier).where(Supplier.company_id == company_id, Supplier.code == code)
    )
    if row:
        return row
    row = Supplier(
        company_id=company_id,
        code=code,
        name=name,
        contact_name="演示供应商",
        contact_phone="13900000000",
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_material(
    db: Session,
    company_id: int,
    code: str,
    name: str,
    *,
    material_type: str,
    uom: str = "pcs",
) -> Material:
    row = db.scalar(
        select(Material).where(Material.company_id == company_id, Material.code == code)
    )
    if row:
        return row
    row = Material(
        company_id=company_id,
        code=code,
        name=name,
        uom=uom,
        material_type=material_type,
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_warehouse(
    db: Session, company_id: int, code: str, name: str, *, is_default: bool
) -> Warehouse:
    row = db.scalar(
        select(Warehouse).where(Warehouse.company_id == company_id, Warehouse.code == code)
    )
    if row:
        return row
    if is_default:
        for wh in db.scalars(
            select(Warehouse).where(
                Warehouse.company_id == company_id, Warehouse.is_default.is_(True)
            )
        ).all():
            wh.is_default = False
    row = Warehouse(
        company_id=company_id,
        code=code,
        name=name,
        is_default=is_default,
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def seed_company_master(db: Session, company_id: int) -> dict:
    """Seed demo customers/suppliers/materials/warehouse for one company."""
    ensure_currency_cny(db)
    customer = _get_or_create_customer(db, company_id, "CUS001", "演示客户")
    supplier = _get_or_create_supplier(db, company_id, "SUP001", "演示供应商")
    fg = _get_or_create_material(
        db, company_id, "FG-001", "成品A", material_type="finished"
    )
    rm = _get_or_create_material(
        db, company_id, "RM-001", "原材料铝板", material_type="raw", uom="kg"
    )
    wh = _get_or_create_warehouse(db, company_id, "WH-MAIN", "主仓库", is_default=True)
    return {
        "customer_id": customer.id,
        "supplier_id": supplier.id,
        "material_ids": [fg.id, rm.id],
        "warehouse_id": wh.id,
    }


def seed_second_company(db: Session, admin_user_id: int) -> Company:
    """Create SECOND company and link admin for isolation smoke tests."""
    company = db.scalar(select(Company).where(Company.code == "SECOND"))
    if company is None:
        company = Company(
            code="SECOND",
            name="第二演示公司",
            base_currency_code="CNY",
            status="active",
        )
        db.add(company)
        db.flush()

    link = db.scalar(
        select(UserCompany).where(
            UserCompany.user_id == admin_user_id,
            UserCompany.company_id == company.id,
        )
    )
    if link is None:
        db.add(
            UserCompany(
                user_id=admin_user_id,
                company_id=company.id,
                is_default=False,
            )
        )
        db.flush()

    seed_company_master(db, company.id)
    return company


def run_demo_seed(db: Session, *, with_second_company: bool = False) -> dict:
    """Seed demo master data for DEFAULT company; optional second company."""
    company = db.scalar(select(Company).where(Company.code == "DEFAULT"))
    if company is None:
        raise RuntimeError("DEFAULT company missing; run org seed first")

    master = seed_company_master(db, company.id)
    result: dict = {
        "company_id": company.id,
        "company_code": company.code,
        "master": master,
        "second_company_id": None,
    }

    if with_second_company:
        admin = db.scalar(select(User).where(User.username == "admin"))
        if admin is None:
            raise RuntimeError("admin user missing; run org seed first")
        second = seed_second_company(db, admin.id)
        result["second_company_id"] = second.id
        result["second_company_code"] = second.code

    db.commit()
    return result
