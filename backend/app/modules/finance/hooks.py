"""Wire finance side-effects into trade posting hooks."""

from app.modules.finance import services as finance_services
from app.modules.trade import services as trade_services


def register_finance_hooks() -> None:
    """Attach AP/AR creation callbacks to stock post services."""
    trade_services.after_stock_in_posted = finance_services.create_ap_from_stock_in
    trade_services.after_stock_out_posted = finance_services.create_ar_from_stock_out
