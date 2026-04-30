from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDialog, QComboBox, QDoubleSpinBox, QFormLayout, QDialogButtonBox,
    QMessageBox, QScrollArea,
)
from PyQt6.QtCore import Qt


def _fmt_brl(value: float) -> str:
    signal = "-" if value < 0 else ""
    return f"{signal}R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MONTH_NAMES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
               "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


class BudgetDialog(QDialog):
    def __init__(self, db, user_id: int, month: int, year: int, budget: dict = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.month = month
        self.year = year
        self.budget = budget
        self.setWindowTitle("Definir Orçamento")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._build_ui()
        if budget:
            self._populate(budget)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        period_lbl = QLabel(f"Período: {MONTH_NAMES[self.month-1]} / {self.year}")
        period_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151; "
                                 "background: #F1F5F9; border-radius: 6px; padding: 8px 12px;")
        layout.addWidget(period_lbl)

        form = QFormLayout()
        form.setSpacing(12)

        # Category (expense only)
        self.cat_combo = QComboBox()
        cats = self.db.get_categories(self.user_id, "expense")
        self._cats = cats
        for c in cats:
            self.cat_combo.addItem(f"{c.get('icon','')} {c['name']}", c["id"])
        form.addRow("Categoria *", self.cat_combo)

        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("R$ ")
        self.amount_spin.setValue(500.0)
        form.addRow("Limite Mensal *", self.amount_spin)

        layout.addLayout(form)

        btns = QDialogButtonBox()
        btn_save = btns.addButton("Salvar", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_save.setDefault(True)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, b: dict):
        idx = self.cat_combo.findData(b["category_id"])
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        self.amount_spin.setValue(b["amount"])

    def _save(self):
        category_id = self.cat_combo.currentData()
        amount = self.amount_spin.value()
        if not category_id:
            QMessageBox.warning(self, "Atenção", "Selecione uma categoria.")
            return
        ok = self.db.save_budget(self.user_id, category_id, amount, self.month, self.year)
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar o orçamento.")


class BudgetCard(QFrame):
    def __init__(self, budget: dict, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(110)
        self._build(budget, on_edit, on_delete)

    def _build(self, b, on_edit, on_delete):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        color = b.get("color") or "#3B82F6"
        icon = b.get("icon") or "💸"
        spent = b.get("spent") or 0.0
        limit = b["amount"]
        pct = min((spent / limit * 100) if limit else 0, 100)

        # Header
        hdr = QHBoxLayout()
        icon_name = QHBoxLayout()
        icon_name.setSpacing(8)
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"background: {color}22; border-radius: 16px; font-size: 16px;")
        name_lbl = QLabel(b.get("category_name", "—"))
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        icon_name.addWidget(icon_lbl)
        icon_name.addWidget(name_lbl)
        hdr.addLayout(icon_name)
        hdr.addStretch()

        btn_edit = QPushButton("✏️")
        btn_edit.setObjectName("btn-icon")
        btn_edit.setFixedSize(28, 28)
        btn_edit.clicked.connect(on_edit)
        btn_del = QPushButton("🗑️")
        btn_del.setObjectName("btn-icon")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(on_delete)
        hdr.addWidget(btn_edit)
        hdr.addWidget(btn_del)
        layout.addLayout(hdr)

        # Amounts
        amounts = QHBoxLayout()
        spent_lbl = QLabel(f"Gasto: {_fmt_brl(spent)}")
        spent_color = "#DC2626" if pct >= 90 else "#F97316" if pct >= 70 else "#334155"
        spent_lbl.setStyleSheet(f"font-size: 12px; color: {spent_color}; font-weight: 500;")
        limit_lbl = QLabel(f"Limite: {_fmt_brl(limit)}")
        limit_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        pct_lbl = QLabel(f"{pct:.0f}%")
        pct_color = "#DC2626" if pct >= 90 else "#F97316" if pct >= 70 else "#059669"
        pct_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {pct_color};")
        amounts.addWidget(spent_lbl)
        amounts.addStretch()
        amounts.addWidget(limit_lbl)
        amounts.addSpacing(8)
        amounts.addWidget(pct_lbl)
        layout.addLayout(amounts)

        # Progress bar
        bar_bg = QFrame()
        bar_bg.setFixedHeight(8)
        bar_bg.setStyleSheet("background: #F1F5F9; border-radius: 4px;")
        bar_bg_lay = QHBoxLayout(bar_bg)
        bar_bg_lay.setContentsMargins(0, 0, 0, 0)
        bar_bg_lay.setSpacing(0)

        bar_color = "#DC2626" if pct >= 90 else "#F97316" if pct >= 70 else color
        bar = QFrame()
        bar.setFixedHeight(8)
        bar.setStyleSheet(f"background: {bar_color}; border-radius: 4px;")
        width = max(int(pct), 0)
        bar.setMinimumWidth(0)
        bar.setSizePolicy(
            bar.sizePolicy().horizontalPolicy(),
            bar.sizePolicy().verticalPolicy(),
        )
        bar_bg_lay.addWidget(bar, int(pct))
        bar_bg_lay.addStretch(100 - int(pct))
        layout.addWidget(bar_bg)

        if pct >= 100:
            warning = QLabel("⚠️ Limite ultrapassado!")
            warning.setStyleSheet("color: #DC2626; font-size: 11px; font-weight: 600;")
            layout.addWidget(warning)


class BudgetsWidget(QWidget):
    def __init__(self, db, user_id: int):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        title = QLabel("Orçamentos Mensais")
        title.setObjectName("title-label")

        lbl_per = QLabel("Período:")
        lbl_per.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")

        self.month_combo = QComboBox()
        for i, m in enumerate(MONTH_NAMES, 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.setMinimumWidth(120)

        self.year_combo = QComboBox()
        cur = datetime.now().year
        for y in range(cur - 2, cur + 3):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(cur))
        self.year_combo.setMinimumWidth(80)

        btn_filter = QPushButton("Filtrar")
        btn_filter.setObjectName("btn-secondary")
        btn_filter.clicked.connect(self.refresh)

        btn_add = QPushButton("+ Novo Orçamento")
        btn_add.clicked.connect(self._add_budget)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(lbl_per)
        toolbar.addWidget(self.month_combo)
        toolbar.addWidget(self.year_combo)
        toolbar.addWidget(btn_filter)
        toolbar.addWidget(btn_add)
        root.addLayout(toolbar)

        # Summary strip
        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("card")
        sum_lay = QHBoxLayout(self.summary_frame)
        sum_lay.setContentsMargins(16, 10, 16, 10)
        self.lbl_total_budget = QLabel("Total orçado: R$ 0,00")
        self.lbl_total_budget.setStyleSheet("font-size: 13px; font-weight: 600; color: #0F172A;")
        self.lbl_total_spent = QLabel("Total gasto: R$ 0,00")
        self.lbl_total_spent.setStyleSheet("font-size: 13px; font-weight: 600; color: #DC2626;")
        self.lbl_remaining = QLabel("Disponível: R$ 0,00")
        self.lbl_remaining.setStyleSheet("font-size: 13px; font-weight: 700; color: #059669;")
        sum_lay.addWidget(self.lbl_total_budget)
        sum_lay.addSpacing(32)
        sum_lay.addWidget(self.lbl_total_spent)
        sum_lay.addSpacing(32)
        sum_lay.addWidget(self.lbl_remaining)
        sum_lay.addStretch()
        root.addWidget(self.summary_frame)

        # Scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        root.addWidget(scroll, 1)

    def refresh(self):
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()
        budgets = self.db.get_budgets(self.user_id, month, year)

        total_budget = sum(b["amount"] for b in budgets)
        total_spent = sum(b.get("spent") or 0 for b in budgets)
        remaining = total_budget - total_spent
        rem_color = "#059669" if remaining >= 0 else "#DC2626"

        self.lbl_total_budget.setText(f"Total orçado: {_fmt_brl(total_budget)}")
        self.lbl_total_spent.setText(f"Total gasto: {_fmt_brl(total_spent)}")
        self.lbl_remaining.setText(f"Disponível: {_fmt_brl(remaining)}")
        self.lbl_remaining.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {rem_color};")

        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not budgets:
            empty = QLabel("Nenhum orçamento definido para este período.\nClique em '+ Novo Orçamento' para começar.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 14px; padding: 40px;")
            self.cards_layout.insertWidget(0, empty)
            return

        # Two-column layout using rows
        row_idx = 0
        col_idx = 0
        current_row_layout = None

        for i, bgt in enumerate(budgets):
            b = dict(bgt)
            if col_idx == 0:
                row_w = QWidget()
                row_w.setStyleSheet("background: transparent;")
                current_row_layout = QHBoxLayout(row_w)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setSpacing(12)
                self.cards_layout.insertWidget(row_idx, row_w)
                row_idx += 1

            card = BudgetCard(
                b,
                on_edit=lambda checked=False, bb=b: self._edit_budget(bb),
                on_delete=lambda checked=False, bb=b: self._delete_budget(bb),
            )
            current_row_layout.addWidget(card)
            col_idx += 1
            if col_idx >= 2:
                col_idx = 0

        if col_idx == 1 and current_row_layout:
            current_row_layout.addStretch()

    def _add_budget(self):
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()
        dlg = BudgetDialog(self.db, self.user_id, month, year, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_budget(self, budget: dict):
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()
        dlg = BudgetDialog(self.db, self.user_id, month, year, budget=budget, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_budget(self, budget: dict):
        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir o orçamento de \"{budget.get('category_name', '?')}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_budget(budget["id"]):
                self.refresh()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir o orçamento.")
