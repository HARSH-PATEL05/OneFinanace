from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import crud, models
from redis_client import redis_safe_get


def safe_float(v) -> float:
    try:
        return float(str(v))
    except Exception:
        return 0.0


def get_user_financial_context(db: Session) -> dict:
    """
    Pulls real financial data from the existing DB and Redis.
    Returns a dict used to build the Sahayak system prompt.
    Falls back gracefully if any query fails.
    """

    context = {
        "total_balance": 0.0,
        "accounts": [],
        "monthly_income": 0.0,
        "monthly_expenses": 0.0,
        "recent_transactions": [],
        "holdings": [],
        "mutual_funds": [],
        "portfolio_value": 0.0,
    }

    # ── 1. Accounts + balances (Redis-enhanced, same as account_route.py) ──
    try:
        accounts = crud.list_accounts(db)
        total_balance = 0.0

        for acc in accounts:
            # Try Redis first, fall back to DB value
            raw = redis_safe_get(f"balance:{acc.account_number}")
            if raw is not None:
                balance = safe_float(raw)
            else:
                balance = safe_float(acc.current_balance)

            total_balance += balance
            context["accounts"].append({
                "bank": acc.bank_name,
                "acronym": acc.acronym,
                "balance": balance,
            })

        context["total_balance"] = total_balance
    except Exception:
        pass

    # ── 2. Monthly income and expenses from transactions ──
    try:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        all_txns = crud.get_transactions(db)  # returns synced transactions only

        monthly_income = 0.0
        monthly_expenses = 0.0
        recent = []

        for txn in all_txns:
            # Monthly totals
            if txn.txn_datetime and txn.txn_datetime >= month_start:
                if txn.type == "credit":
                    monthly_income += safe_float(txn.amount)
                elif txn.type == "debit":
                    monthly_expenses += safe_float(txn.amount)

            # Last 5 transactions for context
            if len(recent) < 5:
                recent.append({
                    "type": txn.type,
                    "amount": safe_float(txn.amount),
                    "description": txn.description or txn.mode or "—",
                    "date": txn.txn_datetime.strftime("%d %b") if txn.txn_datetime else "—",
                    "bank": txn.bankName or "—",
                })

        context["monthly_income"] = monthly_income
        context["monthly_expenses"] = monthly_expenses
        context["recent_transactions"] = recent
    except Exception:
        pass

    # ── 3. Stock holdings ──
    try:
        holdings = db.query(models.Holding).all()
        portfolio_value = 0.0

        for h in holdings:
            current_value = safe_float(h.Ltp) * safe_float(h.Qty)
            invested_value = safe_float(h.average_price) * safe_float(h.Qty)
            pnl = current_value - invested_value
            portfolio_value += current_value

            context["holdings"].append({
                "symbol": h.symbol,
                "name": h.name or h.symbol,
                "qty": safe_float(h.Qty),
                "avg_price": safe_float(h.average_price),
                "ltp": safe_float(h.Ltp),
                "current_value": round(current_value, 2),
                "pnl": round(pnl, 2),
            })

        context["portfolio_value"] = round(portfolio_value, 2)
    except Exception:
        pass

    # ── 4. Mutual funds ──
    try:
        mfs = db.query(models.MutualFund).all()
        for mf in mfs:
            current_value = safe_float(mf.Ltp) * safe_float(mf.Qty)
            context["mutual_funds"].append({
                "fund": mf.fund,
                "symbol": mf.symbol,
                "qty": safe_float(mf.Qty),
                "ltp": safe_float(mf.Ltp),
                "current_value": round(current_value, 2),
            })
    except Exception:
        pass

    return context


def build_context_block(context: dict) -> str:
    """
    Converts the context dict into a readable string
    that gets injected into Sahayak's system prompt.
    """

    lines = ["📊 User's current financial snapshot:"]

    # Balances
    if context["accounts"]:
        lines.append(f"\nBank accounts (total ₹{context['total_balance']:,.2f}):")
        for acc in context["accounts"]:
            lines.append(f"  • {acc['bank']} ({acc['acronym']}): ₹{acc['balance']:,.2f}")
    else:
        lines.append("\nNo bank accounts linked yet.")

    # Monthly summary
    lines.append(f"\nThis month:")
    lines.append(f"  • Income:   ₹{context['monthly_income']:,.2f}")
    lines.append(f"  • Expenses: ₹{context['monthly_expenses']:,.2f}")
    savings = context["monthly_income"] - context["monthly_expenses"]
    lines.append(f"  • Savings:  ₹{savings:,.2f}")

    # Recent transactions
    if context["recent_transactions"]:
        lines.append("\nRecent transactions:")
        for txn in context["recent_transactions"]:
            sign = "+" if txn["type"] == "credit" else "-"
            lines.append(f"  • {txn['date']} | {sign}₹{txn['amount']:,.2f} | {txn['description']}")

    # Stock portfolio
    if context["holdings"]:
        lines.append(f"\nStock portfolio (₹{context['portfolio_value']:,.2f} total):")
        for h in context["holdings"]:
            pnl_sign = "+" if h["pnl"] >= 0 else ""
            lines.append(f"  • {h['symbol']}: {h['qty']} shares @ ₹{h['ltp']} | P&L: {pnl_sign}₹{h['pnl']:,.2f}")

    # Mutual funds
    if context["mutual_funds"]:
        lines.append("\nMutual funds:")
        for mf in context["mutual_funds"]:
            lines.append(f"  • {mf['fund']}: ₹{mf['current_value']:,.2f}")

    return "\n".join(lines)