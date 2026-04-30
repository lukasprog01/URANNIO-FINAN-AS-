from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QTabWidget, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _fmt_brl(value: float) -> str:
    signal = "-" if value < 0 else ""
    return f"{signal}R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MONTH_NAMES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
MONTH_NAMES_FULL = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


class MplCanvas(FigureCanvas if HAS_MATPLOTLIB else QWidget):
    def __init__(self, width=5, height=3.5, dpi=100):
        if HAS_MATPLOTLIB:
            self.fig = Figure(figsize=(width, height), dpi=dpi)
            self.fig.patch.set_facecolor("#FFFFFF")
            self.axes = self.fig.add_subplot(111)
            super().__init__(self.fig)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            super().__init__()

    def clear(self):
        if HAS_MATPLOTLIB:
            self.axes.clear()
            self.axes.set_facecolor("#FAFCFF")
            for spine in self.axes.spines.values():
                spine.set_visible(False)


class ReportsWidget(QWidget):
    def __init__(self, db, user_id: int):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        if not HAS_MATPLOTLIB:
            warn = QLabel(
                "⚠️ matplotlib não encontrado.\n"
                "Instale com:  pip install matplotlib\n"
                "Depois reinicie o aplicativo."
            )
            warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn.setStyleSheet(
                "background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; "
                "padding: 30px; font-size: 14px; color: #92400E;"
            )
            root.addWidget(warn)
            return

        # ── Toolbar ────────────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("card")
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(16, 10, 16, 10)
        tb_lay.setSpacing(10)

        lbl = QLabel("Período:")
        lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")

        self.month_combo = QComboBox()
        for i, m in enumerate(MONTH_NAMES_FULL, 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.setMinimumWidth(120)

        self.year_combo = QComboBox()
        cur = datetime.now().year
        for y in range(cur - 4, cur + 2):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(cur))
        self.year_combo.setMinimumWidth(80)

        btn_refresh = QPushButton("Atualizar")
        btn_refresh.setObjectName("btn-secondary")
        btn_refresh.clicked.connect(self.refresh)

        tb_lay.addWidget(lbl)
        tb_lay.addWidget(self.month_combo)
        tb_lay.addWidget(self.year_combo)
        tb_lay.addWidget(btn_refresh)
        tb_lay.addStretch()
        root.addWidget(toolbar)

        # ── Tabs ───────────────────────────────────────────────────────────
        self.tabs = QTabWidget()

        self.tabs.addTab(self._build_overview_tab(), "📊  Visão Geral")
        self.tabs.addTab(self._build_expense_tab(), "💸  Despesas")
        self.tabs.addTab(self._build_income_tab(), "💰  Receitas")
        self.tabs.addTab(self._build_annual_tab(), "📅  Anual")

        root.addWidget(self.tabs, 1)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    def _build_overview_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Summary cards
        cards_row = QHBoxLayout()
        self.ov_income = self._stat_card("💰 Receitas", "R$ 0,00", "#059669", "#ECFDF5")
        self.ov_expense = self._stat_card("💸 Despesas", "R$ 0,00", "#DC2626", "#FEF2F2")
        self.ov_balance = self._stat_card("⚖️ Saldo", "R$ 0,00", "#7C3AED", "#F5F3FF")
        self.ov_savings_rate = self._stat_card("🎯 Taxa de Poupança", "0%", "#0369A1", "#EFF6FF")
        for c in [self.ov_income, self.ov_expense, self.ov_balance, self.ov_savings_rate]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # Bar chart: income vs expense
        self.ov_canvas = MplCanvas(width=8, height=3.5)
        card = QFrame()
        card.setObjectName("card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(12, 12, 12, 12)
        lbl = QLabel("Receitas vs Despesas")
        lbl.setObjectName("title-label")
        card_lay.addWidget(lbl)
        card_lay.addWidget(self.ov_canvas)
        layout.addWidget(card, 1)

        return w

    def _build_expense_tab(self):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Pie chart
        self.exp_canvas = MplCanvas(width=5, height=4)
        pie_card = QFrame()
        pie_card.setObjectName("card")
        pie_lay = QVBoxLayout(pie_card)
        pie_lay.setContentsMargins(12, 12, 12, 12)
        lbl = QLabel("Distribuição por Categoria")
        lbl.setObjectName("title-label")
        pie_lay.addWidget(lbl)
        pie_lay.addWidget(self.exp_canvas)
        layout.addWidget(pie_card, 1)

        # Legend / list
        self.exp_list_frame = QFrame()
        self.exp_list_frame.setObjectName("card")
        self.exp_list_layout = QVBoxLayout(self.exp_list_frame)
        self.exp_list_layout.setContentsMargins(16, 16, 16, 16)
        self.exp_list_layout.setSpacing(10)
        lbl2 = QLabel("Detalhamento")
        lbl2.setObjectName("title-label")
        self.exp_list_layout.addWidget(lbl2)
        self.exp_list_layout.addStretch()
        layout.addWidget(self.exp_list_frame, 1)

        return w

    def _build_income_tab(self):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.inc_canvas = MplCanvas(width=5, height=4)
        pie_card = QFrame()
        pie_card.setObjectName("card")
        pie_lay = QVBoxLayout(pie_card)
        pie_lay.setContentsMargins(12, 12, 12, 12)
        lbl = QLabel("Distribuição de Receitas")
        lbl.setObjectName("title-label")
        pie_lay.addWidget(lbl)
        pie_lay.addWidget(self.inc_canvas)
        layout.addWidget(pie_card, 1)

        self.inc_list_frame = QFrame()
        self.inc_list_frame.setObjectName("card")
        self.inc_list_layout = QVBoxLayout(self.inc_list_frame)
        self.inc_list_layout.setContentsMargins(16, 16, 16, 16)
        self.inc_list_layout.setSpacing(10)
        lbl2 = QLabel("Detalhamento")
        lbl2.setObjectName("title-label")
        self.inc_list_layout.addWidget(lbl2)
        self.inc_list_layout.addStretch()
        layout.addWidget(self.inc_list_frame, 1)

        return w

    def _build_annual_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.annual_canvas = MplCanvas(width=9, height=4)
        card = QFrame()
        card.setObjectName("card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(12, 12, 12, 12)
        lbl = QLabel("Evolução Mensal do Ano")
        lbl.setObjectName("title-label")
        card_lay.addWidget(lbl)
        card_lay.addWidget(self.annual_canvas)
        layout.addWidget(card, 1)

        return w

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _stat_card(self, label, value, color, bg):
        frame = QFrame()
        frame.setObjectName("stat-card")
        frame.setMinimumHeight(80)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {color};")
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; color: #64748B;")

        lay.addWidget(val_lbl)
        lay.addWidget(lbl)

        frame._val_lbl = val_lbl
        frame._color = color
        return frame

    # ── Refresh ────────────────────────────────────────────────────────────────
    def refresh(self):
        if not HAS_MATPLOTLIB:
            return

        month = self.month_combo.currentData()
        year = self.year_combo.currentData()

        summary = self.db.get_monthly_summary(self.user_id, month, year)
        exp_cats = self.db.get_expense_by_category(self.user_id, month, year)
        inc_cats = self.db.get_income_by_category(self.user_id, month, year)
        yearly = self.db.get_yearly_summary(self.user_id, year)

        self._refresh_overview(summary)
        self._refresh_expenses(exp_cats, summary["expense"])
        self._refresh_income(inc_cats, summary["income"])
        self._refresh_annual(yearly)

    def _refresh_overview(self, summary):
        income = summary["income"]
        expense = summary["expense"]
        balance = summary["balance"]
        savings_rate = (balance / income * 100) if income else 0

        bal_color = "#059669" if balance >= 0 else "#DC2626"

        self.ov_income._val_lbl.setText(_fmt_brl(income))
        self.ov_expense._val_lbl.setText(_fmt_brl(expense))
        self.ov_balance._val_lbl.setText(_fmt_brl(balance))
        self.ov_balance._val_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {bal_color};")
        self.ov_savings_rate._val_lbl.setText(f"{savings_rate:.1f}%")

        canvas = self.ov_canvas
        canvas.clear()
        ax = canvas.axes

        categories = ["Receitas", "Despesas", "Saldo"]
        values = [income, expense, abs(balance)]
        colors_list = ["#10B981", "#EF4444", "#059669" if balance >= 0 else "#DC2626"]

        bars = ax.bar(categories, values, color=colors_list, width=0.5,
                      edgecolor="none", zorder=3)
        ax.set_ylabel("Valor (R$)", fontsize=10, color="#64748B")
        ax.tick_params(colors="#64748B", labelsize=9)
        ax.grid(axis="y", color="#F1F5F9", linewidth=1, zorder=0)
        ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 100)

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                    _fmt_brl(val), ha="center", va="bottom", fontsize=9, color="#334155",
                    fontweight="bold")

        canvas.fig.tight_layout()
        canvas.draw()

    def _refresh_expenses(self, cats, total):
        canvas = self.exp_canvas
        canvas.clear()
        ax = canvas.axes

        while self.exp_list_layout.count() > 2:
            item = self.exp_list_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        if not cats:
            ax.text(0.5, 0.5, "Sem despesas neste período", ha="center", va="center",
                    transform=ax.transAxes, color="#94A3B8", fontsize=12)
            canvas.draw()
            return

        labels = [c["name"] for c in cats]
        values = [c["total"] for c in cats]
        colors_list = [c.get("color") or "#3B82F6" for c in cats]

        wedges, _ = ax.pie(values, colors=colors_list, startangle=90,
                           wedgeprops=dict(edgecolor="white", linewidth=2))

        for i, (cat, val) in enumerate(zip(cats, values)):
            pct = val / total * 100 if total else 0
            row = QFrame()
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(8)

            dot = QLabel("●")
            color = cat.get("color") or "#3B82F6"
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            dot.setFixedWidth(16)

            icon = cat.get("icon") or ""
            name = QLabel(f"{icon} {cat['name']}")
            name.setStyleSheet("font-size: 12px; color: #334155;")
            amount = QLabel(_fmt_brl(val))
            amount.setStyleSheet("font-size: 12px; font-weight: 600; color: #DC2626;")
            pct_lbl = QLabel(f"{pct:.1f}%")
            pct_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")

            row_lay.addWidget(dot)
            row_lay.addWidget(name)
            row_lay.addStretch()
            row_lay.addWidget(amount)
            row_lay.addWidget(pct_lbl)
            self.exp_list_layout.insertWidget(i + 1, row)

        canvas.fig.tight_layout()
        canvas.draw()

    def _refresh_income(self, cats, total):
        canvas = self.inc_canvas
        canvas.clear()
        ax = canvas.axes

        while self.inc_list_layout.count() > 2:
            item = self.inc_list_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        if not cats:
            ax.text(0.5, 0.5, "Sem receitas neste período", ha="center", va="center",
                    transform=ax.transAxes, color="#94A3B8", fontsize=12)
            canvas.draw()
            return

        labels = [c["name"] for c in cats]
        values = [c["total"] for c in cats]
        colors_list = [c.get("color") or "#10B981" for c in cats]

        ax.pie(values, colors=colors_list, startangle=90,
               wedgeprops=dict(edgecolor="white", linewidth=2))

        for i, (cat, val) in enumerate(zip(cats, values)):
            pct = val / total * 100 if total else 0
            row = QFrame()
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(8)

            dot = QLabel("●")
            color = cat.get("color") or "#10B981"
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            dot.setFixedWidth(16)

            icon = cat.get("icon") or ""
            name = QLabel(f"{icon} {cat['name']}")
            name.setStyleSheet("font-size: 12px; color: #334155;")
            amount = QLabel(_fmt_brl(val))
            amount.setStyleSheet("font-size: 12px; font-weight: 600; color: #059669;")
            pct_lbl = QLabel(f"{pct:.1f}%")
            pct_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")

            row_lay.addWidget(dot)
            row_lay.addWidget(name)
            row_lay.addStretch()
            row_lay.addWidget(amount)
            row_lay.addWidget(pct_lbl)
            self.inc_list_layout.insertWidget(i + 1, row)

        canvas.fig.tight_layout()
        canvas.draw()

    def _refresh_annual(self, yearly):
        year = self.year_combo.currentData()
        canvas = self.annual_canvas
        canvas.clear()
        ax = canvas.axes

        month_data = {r["month"]: r for r in yearly}
        months = list(range(1, 13))
        incomes = [month_data.get(m, {}).get("income", 0) for m in months]
        expenses = [month_data.get(m, {}).get("expense", 0) for m in months]

        x = range(len(months))
        width = 0.35

        bars1 = ax.bar([i - width/2 for i in x], incomes, width,
                       label="Receitas", color="#10B981", edgecolor="none", zorder=3)
        bars2 = ax.bar([i + width/2 for i in x], expenses, width,
                       label="Despesas", color="#EF4444", edgecolor="none", zorder=3)

        ax.set_xticks(list(x))
        ax.set_xticklabels(MONTH_NAMES, fontsize=9, color="#64748B")
        ax.tick_params(colors="#64748B", labelsize=9)
        ax.set_ylabel("Valor (R$)", fontsize=10, color="#64748B")
        ax.grid(axis="y", color="#F1F5F9", linewidth=1, zorder=0)
        ax.set_title(f"Receitas vs Despesas — {year}", fontsize=12, color="#334155", pad=10)
        ax.legend(fontsize=10, framealpha=0)

        canvas.fig.tight_layout()
        canvas.draw()
