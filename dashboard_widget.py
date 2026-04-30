from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont


def _fmt_brl(value: float) -> str:
    signal = "-" if value < 0 else ""
    return f"{signal}R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class StatCard(QFrame):
    def __init__(self, icon: str, label: str, value: str, color: str, bg: str):
        super().__init__()
        self.setObjectName("stat-card")
        self.setMinimumHeight(110)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("stat-icon")
        icon_lbl.setFixedSize(52, 52)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {bg}; border-radius: 26px; font-size: 24px;"
        )

        right = QVBoxLayout()
        right.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat-value")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700;")

        lbl = QLabel(label)
        lbl.setObjectName("stat-label")

        right.addWidget(val_lbl)
        right.addWidget(lbl)

        layout.addWidget(icon_lbl)
        layout.addLayout(right)
        layout.addStretch()

        self.val_lbl = val_lbl

    def set_value(self, value: str):
        self.val_lbl.setText(value)


class DashboardWidget(QWidget):
    def __init__(self, db, user_id: int):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── Stat cards ─────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_balance = StatCard("💰", "Saldo Total", "R$ 0,00", "#0F172A", "#EFF6FF")
        self.card_income = StatCard("📈", "Receitas do Mês", "R$ 0,00", "#059669", "#ECFDF5")
        self.card_expense = StatCard("📉", "Despesas do Mês", "R$ 0,00", "#DC2626", "#FEF2F2")
        self.card_savings = StatCard("🎯", "Saldo do Mês", "R$ 0,00", "#7C3AED", "#F5F3FF")

        for card in [self.card_balance, self.card_income, self.card_expense, self.card_savings]:
            cards_row.addWidget(card)

        layout.addLayout(cards_row)

        # ── Middle row: recent transactions + category breakdown ───────────
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        mid_row.addWidget(self._build_recent_transactions(), 3)
        mid_row.addWidget(self._build_category_breakdown(), 2)

        layout.addLayout(mid_row)

        # ── Account balances ───────────────────────────────────────────────
        layout.addWidget(self._build_account_balances())

        layout.addStretch()

    def _build_recent_transactions(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Últimas Transações")
        title.setObjectName("title-label")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setHorizontalHeaderLabels(["Data", "Categoria", "Conta", "Descrição", "Valor"])
        self.recent_table.horizontalHeader().setStretchLastSection(False)
        self.recent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setMinimumHeight(280)
        self.recent_table.setShowGrid(False)
        self.recent_table.verticalHeader().setDefaultSectionSize(40)

        layout.addWidget(self.recent_table)
        return card

    def _build_category_breakdown(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(10)

        title = QLabel("Despesas por Categoria")
        title.setObjectName("title-label")
        layout.addWidget(title)

        self.cat_layout = QVBoxLayout()
        self.cat_layout.setSpacing(8)
        layout.addLayout(self.cat_layout)
        layout.addStretch()

        return card

    def _build_account_balances(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        title = QLabel("Saldo por Conta")
        title.setObjectName("title-label")
        layout.addWidget(title)

        self.accounts_row = QHBoxLayout()
        self.accounts_row.setSpacing(12)
        layout.addLayout(self.accounts_row)

        return card

    # ── Refresh ────────────────────────────────────────────────────────────────
    def refresh(self):
        now = datetime.now()
        month, year = now.month, now.year

        total_balance = self.db.get_total_balance(self.user_id)
        summary = self.db.get_monthly_summary(self.user_id, month, year)
        recent = self.db.get_transactions(self.user_id, limit=10)
        cats = self.db.get_expense_by_category(self.user_id, month, year)
        accounts = self.db.get_accounts(self.user_id)

        self.card_balance.set_value(_fmt_brl(total_balance))
        self.card_income.set_value(_fmt_brl(summary["income"]))
        self.card_expense.set_value(_fmt_brl(summary["expense"]))

        balance_color = "#059669" if summary["balance"] >= 0 else "#DC2626"
        self.card_savings.val_lbl.setStyleSheet(
            f"color: {balance_color}; font-size: 22px; font-weight: 700;"
        )
        self.card_savings.set_value(_fmt_brl(summary["balance"]))

        self._refresh_recent(recent)
        self._refresh_categories(cats, summary["expense"])
        self._refresh_accounts(accounts)

    def _refresh_recent(self, transactions):
        self.recent_table.setRowCount(0)
        month_names = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

        for t in transactions:
            row = self.recent_table.rowCount()
            self.recent_table.insertRow(row)

            try:
                d = datetime.strptime(t["date"], "%Y-%m-%d")
                date_str = f"{d.day:02d} {month_names[d.month-1]}"
            except Exception:
                date_str = t["date"]

            cat_icon = t.get("category_icon", "") or ""
            cat_name = t.get("category_name", "—") or "—"
            acct_name = t.get("account_name", "—") or "—"
            desc = t.get("description", "") or ""
            amount = t["amount"]
            is_income = t["type"] == "income"

            items = [
                (date_str, Qt.AlignmentFlag.AlignCenter),
                (f"{cat_icon} {cat_name}", Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (acct_name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (desc, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (_fmt_brl(amount), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]

            for col, (text, align) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                if col == 4:
                    item.setForeground(QColor("#059669" if is_income else "#DC2626"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.recent_table.setItem(row, col, item)

        for col, w in enumerate([90, 130, 120, 0, 110]):
            if w:
                self.recent_table.setColumnWidth(col, w)

    def _refresh_categories(self, cats, total_expense):
        while self.cat_layout.count():
            item = self.cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cats:
            empty = QLabel("Nenhuma despesa este mês")
            empty.setStyleSheet("color: #94A3B8; font-size: 13px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cat_layout.addWidget(empty)
            return

        for cat in cats[:8]:
            pct = (cat["total"] / total_expense * 100) if total_expense else 0

            row = QWidget()
            row_lay = QVBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(4)

            top = QHBoxLayout()
            name = QLabel(f"{cat.get('icon','') or ''} {cat['name']}")
            name.setStyleSheet("font-size: 12px; color: #334155; font-weight: 500;")
            amount = QLabel(_fmt_brl(cat["total"]))
            amount.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: 600;")
            pct_lbl = QLabel(f"{pct:.1f}%")
            pct_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
            top.addWidget(name)
            top.addStretch()
            top.addWidget(amount)
            top.addSpacing(6)
            top.addWidget(pct_lbl)

            # Progress bar
            bar_bg = QFrame()
            bar_bg.setFixedHeight(5)
            bar_bg.setStyleSheet("background: #F1F5F9; border-radius: 3px;")
            bar_bg_lay = QHBoxLayout(bar_bg)
            bar_bg_lay.setContentsMargins(0, 0, 0, 0)
            bar_bg_lay.setSpacing(0)

            color = cat.get("color") or "#3B82F6"
            bar = QFrame()
            bar.setFixedHeight(5)
            fill = max(int(pct), 1)
            bar.setFixedWidth(int(fill * 2))
            bar.setStyleSheet(f"background: {color}; border-radius: 3px;")
            bar_bg_lay.addWidget(bar)
            bar_bg_lay.addStretch()

            row_lay.addLayout(top)
            row_lay.addWidget(bar_bg)
            self.cat_layout.addWidget(row)

    def _refresh_accounts(self, accounts):
        while self.accounts_row.count():
            item = self.accounts_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        type_icons = {
            "checking": "🏦",
            "savings": "🏧",
            "credit": "💳",
            "cash": "💵",
            "investment": "📈",
        }
        type_labels = {
            "checking": "Conta Corrente",
            "savings": "Poupança",
            "credit": "Cartão de Crédito",
            "cash": "Dinheiro",
            "investment": "Investimento",
        }

        for acct in accounts:
            card = QFrame()
            card.setObjectName("stat-card")
            card.setMinimumWidth(160)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(16, 14, 16, 14)
            lay.setSpacing(6)

            color = acct.get("color") or "#3B82F6"
            icon = type_icons.get(acct["type"], "💰")

            icon_lbl = QLabel(icon)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setFixedSize(40, 40)
            icon_lbl.setStyleSheet(
                f"background: {color}22; border-radius: 20px; font-size: 20px;"
            )

            name_lbl = QLabel(acct["name"])
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
            name_lbl.setWordWrap(True)

            type_lbl = QLabel(type_labels.get(acct["type"], acct["type"]))
            type_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")

            bal = acct["balance"]
            bal_color = "#059669" if bal >= 0 else "#DC2626"
            bal_lbl = QLabel(_fmt_brl(bal))
            bal_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {bal_color};")

            lay.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignLeft)
            lay.addWidget(name_lbl)
            lay.addWidget(type_lbl)
            lay.addWidget(bal_lbl)

            self.accounts_row.addWidget(card)

        if not accounts:
            empty = QLabel("Nenhuma conta cadastrada")
            empty.setStyleSheet("color: #94A3B8; font-size: 13px;")
            self.accounts_row.addWidget(empty)

        self.accounts_row.addStretch()
