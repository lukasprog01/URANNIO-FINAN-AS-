from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QLineEdit, QDateEdit, QDoubleSpinBox, QTextEdit,
    QFormLayout, QDialogButtonBox, QMessageBox, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont


def _fmt_brl(value: float) -> str:
    signal = "-" if value < 0 else ""
    return f"{signal}R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MONTH_NAMES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
               "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


class TransactionDialog(QDialog):
    def __init__(self, db, user_id: int, transaction: dict = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.transaction = transaction
        self.setWindowTitle("Nova Transação" if not transaction else "Editar Transação")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if transaction:
            self._populate(transaction)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Type selector
        type_row = QHBoxLayout()
        type_lbl = QLabel("Tipo")
        type_lbl.setStyleSheet("font-weight: 600; color: #374151;")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["💰  Receita", "💸  Despesa"])
        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        type_row.addWidget(type_lbl)
        type_row.addWidget(self.type_combo, 1)
        layout.addLayout(type_row)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(1.0)
        self.amount_spin.setPrefix("R$ ")
        self.amount_spin.setValue(0.0)
        form.addRow("Valor *", self.amount_spin)

        # Description
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ex: Supermercado, Salário...")
        form.addRow("Descrição *", self.desc_input)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Data *", self.date_edit)

        # Account
        self.account_combo = QComboBox()
        self._load_accounts()
        form.addRow("Conta", self.account_combo)

        # Category
        self.category_combo = QComboBox()
        self._load_categories("income")
        form.addRow("Categoria", self.category_combo)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Observações opcionais...")
        self.notes_edit.setMaximumHeight(80)
        form.addRow("Notas", self.notes_edit)

        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox()
        btn_save = btns.addButton("Salvar", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_save.setDefault(True)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_accounts(self):
        self.account_combo.clear()
        self.account_combo.addItem("— Selecione —", None)
        accounts = self.db.get_accounts(self.user_id)
        self._accounts = accounts
        for a in accounts:
            self.account_combo.addItem(a["name"], a["id"])

    def _load_categories(self, cat_type: str):
        self.category_combo.clear()
        self.category_combo.addItem("— Selecione —", None)
        cats = self.db.get_categories(self.user_id, cat_type)
        self._categories = cats
        for c in cats:
            self.category_combo.addItem(f"{c.get('icon','')} {c['name']}", c["id"])

    def _on_type_change(self, idx):
        cat_type = "income" if idx == 0 else "expense"
        self._load_categories(cat_type)

    def _populate(self, t: dict):
        self.type_combo.setCurrentIndex(0 if t["type"] == "income" else 1)
        self._on_type_change(0 if t["type"] == "income" else 1)
        self.amount_spin.setValue(t["amount"])
        self.desc_input.setText(t.get("description") or "")
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d").date()
            self.date_edit.setDate(QDate(d.year, d.month, d.day))
        except Exception:
            pass
        if t.get("account_id"):
            idx = self.account_combo.findData(t["account_id"])
            if idx >= 0:
                self.account_combo.setCurrentIndex(idx)
        if t.get("category_id"):
            idx = self.category_combo.findData(t["category_id"])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        self.notes_edit.setPlainText(t.get("notes") or "")

    def _save(self):
        amount = self.amount_spin.value()
        desc = self.desc_input.text().strip()

        if amount <= 0:
            QMessageBox.warning(self, "Atenção", "O valor deve ser maior que zero.")
            return
        if not desc:
            QMessageBox.warning(self, "Atenção", "A descrição é obrigatória.")
            return

        trans_type = "income" if self.type_combo.currentIndex() == 0 else "expense"
        qdate = self.date_edit.date()
        date_str = f"{qdate.year()}-{qdate.month():02d}-{qdate.day():02d}"
        account_id = self.account_combo.currentData()
        category_id = self.category_combo.currentData()
        notes = self.notes_edit.toPlainText().strip() or None

        if self.transaction:
            ok = self.db.update_transaction(
                self.transaction["id"], account_id, category_id,
                trans_type, amount, desc, date_str, notes,
            )
        else:
            ok = self.db.create_transaction(
                self.user_id, account_id, category_id,
                trans_type, amount, desc, date_str, notes,
            )

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar a transação.")


class TransactionsWidget(QWidget):
    def __init__(self, db, user_id: int):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Toolbar ────────────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("card")
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(16, 12, 16, 12)
        tb_lay.setSpacing(10)

        # Month/Year filters
        lbl_per = QLabel("Período:")
        lbl_per.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")

        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(120)
        for i, m in enumerate(MONTH_NAMES, 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)

        self.year_combo = QComboBox()
        self.year_combo.setMinimumWidth(80)
        current_year = datetime.now().year
        for y in range(current_year - 4, current_year + 2):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))

        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.setMinimumWidth(130)
        self.type_filter.addItem("Todos os Tipos", None)
        self.type_filter.addItem("💰 Receitas", "income")
        self.type_filter.addItem("💸 Despesas", "expense")

        # Account filter
        self.account_filter = QComboBox()
        self.account_filter.setMinimumWidth(140)
        self.account_filter.addItem("Todas as Contas", None)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar transação...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._filter_table)

        btn_filter = QPushButton("Filtrar")
        btn_filter.setObjectName("btn-secondary")
        btn_filter.clicked.connect(self.refresh)

        btn_add = QPushButton("+ Nova Transação")
        btn_add.setObjectName("btn-success")
        btn_add.clicked.connect(self._add_transaction)

        tb_lay.addWidget(lbl_per)
        tb_lay.addWidget(self.month_combo)
        tb_lay.addWidget(self.year_combo)
        tb_lay.addWidget(self.type_filter)
        tb_lay.addWidget(self.account_filter)
        tb_lay.addWidget(self.search_input)
        tb_lay.addStretch()
        tb_lay.addWidget(btn_filter)
        tb_lay.addWidget(btn_add)
        layout.addWidget(toolbar)

        # ── Summary bar ────────────────────────────────────────────────────
        summary = QFrame()
        summary.setObjectName("card")
        sum_lay = QHBoxLayout(summary)
        sum_lay.setContentsMargins(16, 10, 16, 10)
        sum_lay.setSpacing(32)

        self.lbl_income = QLabel("Receitas: R$ 0,00")
        self.lbl_income.setStyleSheet("font-size: 13px; font-weight: 600; color: #059669;")
        self.lbl_expense = QLabel("Despesas: R$ 0,00")
        self.lbl_expense.setStyleSheet("font-size: 13px; font-weight: 600; color: #DC2626;")
        self.lbl_balance = QLabel("Saldo: R$ 0,00")
        self.lbl_balance.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        self.lbl_count = QLabel("0 transações")
        self.lbl_count.setStyleSheet("font-size: 12px; color: #94A3B8;")

        sum_lay.addWidget(self.lbl_income)
        sum_lay.addWidget(self.lbl_expense)
        sum_lay.addWidget(self.lbl_balance)
        sum_lay.addStretch()
        sum_lay.addWidget(self.lbl_count)
        layout.addWidget(summary)

        # ── Table ──────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Data", "Tipo", "Categoria", "Conta", "Descrição", "Notas", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.doubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table)

        # ── Action buttons ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️  Editar")
        btn_edit.setObjectName("btn-secondary")
        btn_edit.clicked.connect(self._edit_selected)

        btn_del = QPushButton("🗑️  Excluir")
        btn_del.setObjectName("btn-danger")
        btn_del.clicked.connect(self._delete_selected)

        btn_row.addStretch()
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

        self._transactions = []

    # ── Data loading ───────────────────────────────────────────────────────────
    def refresh(self):
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()
        trans_type = self.type_filter.currentData()
        account_id = self.account_filter.currentData()

        self._load_account_filter()

        self._transactions = self.db.get_transactions(
            self.user_id,
            month=month,
            year=year,
            trans_type=trans_type,
            account_id=account_id,
        )

        self._populate_table(self._transactions)
        self._update_summary(self._transactions)

    def _load_account_filter(self):
        current = self.account_filter.currentData()
        self.account_filter.blockSignals(True)
        self.account_filter.clear()
        self.account_filter.addItem("Todas as Contas", None)
        for a in self.db.get_accounts(self.user_id):
            self.account_filter.addItem(a["name"], a["id"])
        idx = self.account_filter.findData(current)
        if idx >= 0:
            self.account_filter.setCurrentIndex(idx)
        self.account_filter.blockSignals(False)

    def _populate_table(self, transactions):
        self.table.setRowCount(0)
        month_abbr = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

        for t in transactions:
            row = self.table.rowCount()
            self.table.insertRow(row)

            try:
                d = datetime.strptime(t["date"], "%Y-%m-%d")
                date_str = f"{d.day:02d}/{d.month:02d}/{d.year}"
            except Exception:
                date_str = t["date"]

            is_income = t["type"] == "income"
            type_str = "💰 Receita" if is_income else "💸 Despesa"
            type_color = "#059669" if is_income else "#DC2626"
            amount_color = "#059669" if is_income else "#DC2626"

            cat_icon = t.get("category_icon") or ""
            cat_name = t.get("category_name") or "—"
            acct_name = t.get("account_name") or "—"
            desc = t.get("description") or ""
            notes = t.get("notes") or ""

            vals = [
                (date_str, Qt.AlignmentFlag.AlignCenter),
                (type_str, Qt.AlignmentFlag.AlignCenter),
                (f"{cat_icon} {cat_name}", Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (acct_name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (desc, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (notes, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (_fmt_brl(t["amount"]), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]

            for col, (text, align) in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.ItemDataRole.UserRole, t["id"])
                if col == 1:
                    item.setForeground(QColor(type_color))
                    f = item.font(); f.setBold(True); item.setFont(f)
                if col == 6:
                    item.setForeground(QColor(amount_color))
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.table.setItem(row, col, item)

        for col, w in enumerate([100, 110, 140, 130, 0, 120, 120]):
            if w:
                self.table.setColumnWidth(col, w)

    def _update_summary(self, transactions):
        income = sum(t["amount"] for t in transactions if t["type"] == "income")
        expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
        balance = income - expense
        bal_color = "#059669" if balance >= 0 else "#DC2626"

        self.lbl_income.setText(f"Receitas: {_fmt_brl(income)}")
        self.lbl_expense.setText(f"Despesas: {_fmt_brl(expense)}")
        self.lbl_balance.setText(f"Saldo: {_fmt_brl(balance)}")
        self.lbl_balance.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {bal_color};")
        self.lbl_count.setText(f"{len(transactions)} transações")

    def _filter_table(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    # ── CRUD ───────────────────────────────────────────────────────────────────
    def _add_transaction(self):
        dlg = TransactionDialog(self.db, self.user_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Atenção", "Selecione uma transação para editar.")
            return
        trans_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        trans = next((t for t in self._transactions if t["id"] == trans_id), None)
        if not trans:
            return
        dlg = TransactionDialog(self.db, self.user_id, transaction=trans, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Atenção", "Selecione uma transação para excluir.")
            return
        trans_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        desc = self.table.item(row, 4).text()

        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir a transação \"{desc}\"?\n\nEsta ação irá reverter o saldo da conta.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_transaction(trans_id):
                self.refresh()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a transação.")
