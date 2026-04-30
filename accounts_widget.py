from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDialog, QLineEdit, QDoubleSpinBox, QComboBox, QFormLayout,
    QDialogButtonBox, QMessageBox, QGridLayout, QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


def _fmt_brl(value: float) -> str:
    signal = "-" if value < 0 else ""
    return f"{signal}R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


ACCOUNT_TYPES = [
    ("checking", "🏦 Conta Corrente"),
    ("savings", "🏧 Poupança"),
    ("credit", "💳 Cartão de Crédito"),
    ("cash", "💵 Dinheiro"),
    ("investment", "📈 Investimento"),
]

COLOR_OPTIONS = [
    ("#3B82F6", "Azul"),
    ("#10B981", "Verde"),
    ("#8B5CF6", "Roxo"),
    ("#F59E0B", "Amarelo"),
    ("#EF4444", "Vermelho"),
    ("#EC4899", "Rosa"),
    ("#06B6D4", "Ciano"),
    ("#6B7280", "Cinza"),
]


class AccountDialog(QDialog):
    def __init__(self, db, user_id: int, account: dict = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.account = account
        self.setWindowTitle("Nova Conta" if not account else "Editar Conta")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()
        if account:
            self._populate(account)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: Nubank, Bradesco, Carteira...")
        form.addRow("Nome da Conta *", self.name_input)

        # Type
        self.type_combo = QComboBox()
        for key, label in ACCOUNT_TYPES:
            self.type_combo.addItem(label, key)
        form.addRow("Tipo *", self.type_combo)

        # Balance
        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(-999999999, 999999999)
        self.balance_spin.setDecimals(2)
        self.balance_spin.setPrefix("R$ ")
        self.balance_spin.setValue(0.0)
        form.addRow("Saldo Inicial *", self.balance_spin)

        # Color
        self.color_combo = QComboBox()
        for hex_color, name in COLOR_OPTIONS:
            self.color_combo.addItem(f"  ● {name}", hex_color)
        form.addRow("Cor", self.color_combo)

        layout.addLayout(form)

        note = QLabel("⚠️ Alterar o saldo de uma conta existente ajusta o valor\ndirectamente, sem criar transação.")
        note.setStyleSheet("color: #92400E; background: #FFFBEB; border: 1px solid #FDE68A; "
                           "border-radius: 6px; padding: 8px 12px; font-size: 12px;")
        note.setWordWrap(True)
        if not self.account:
            note.setText("O saldo inicial é registrado na conta. Transações futuras\natualizam este saldo automaticamente.")
            note.setStyleSheet("color: #1E40AF; background: #EFF6FF; border: 1px solid #BFDBFE; "
                               "border-radius: 6px; padding: 8px 12px; font-size: 12px;")
        layout.addWidget(note)

        btns = QDialogButtonBox()
        btn_save = btns.addButton("Salvar", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_save.setDefault(True)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, a: dict):
        self.name_input.setText(a["name"])
        idx = self.type_combo.findData(a["type"])
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.balance_spin.setValue(a["balance"])
        idx = self.color_combo.findData(a.get("color", "#3B82F6"))
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Atenção", "O nome da conta é obrigatório.")
            return

        acct_type = self.type_combo.currentData()
        balance = self.balance_spin.value()
        color = self.color_combo.currentData()

        if self.account:
            ok = self.db.update_account(self.account["id"], name, acct_type, balance, color)
        else:
            ok = self.db.create_account(self.user_id, name, acct_type, balance, color)

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar a conta.")


class AccountCard(QFrame):
    def __init__(self, account: dict, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.account = account
        self.setObjectName("card")
        self.setMinimumHeight(160)
        self.setMinimumWidth(220)
        self._build(account, on_edit, on_delete)

    def _build(self, a, on_edit, on_delete):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        type_icons = {
            "checking": "🏦", "savings": "🏧", "credit": "💳",
            "cash": "💵", "investment": "📈",
        }
        type_labels = {
            "checking": "Conta Corrente", "savings": "Poupança",
            "credit": "Cartão de Crédito", "cash": "Dinheiro",
            "investment": "Investimento",
        }

        color = a.get("color") or "#3B82F6"
        icon = type_icons.get(a["type"], "💰")

        # Header
        hdr = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(42, 42)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"background: {color}22; border-radius: 21px; font-size: 22px;")

        top_right = QHBoxLayout()
        top_right.addStretch()

        btn_edit = QPushButton("✏️")
        btn_edit.setObjectName("btn-icon")
        btn_edit.setToolTip("Editar")
        btn_edit.setFixedSize(30, 30)
        btn_edit.clicked.connect(on_edit)

        btn_del = QPushButton("🗑️")
        btn_del.setObjectName("btn-icon")
        btn_del.setToolTip("Excluir")
        btn_del.setFixedSize(30, 30)
        btn_del.clicked.connect(on_delete)

        top_right.addWidget(btn_edit)
        top_right.addWidget(btn_del)

        hdr.addWidget(icon_lbl)
        hdr.addStretch()
        hdr.addLayout(top_right)
        layout.addLayout(hdr)

        # Name
        name_lbl = QLabel(a["name"])
        name_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # Type
        type_lbl = QLabel(type_labels.get(a["type"], a["type"]))
        type_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        layout.addWidget(type_lbl)

        layout.addStretch()

        # Balance
        bal = a["balance"]
        bal_color = "#059669" if bal >= 0 else "#DC2626"
        bal_lbl = QLabel(_fmt_brl(bal))
        bal_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {bal_color};")
        layout.addWidget(bal_lbl)

        # Color strip at bottom
        strip = QFrame()
        strip.setFixedHeight(4)
        strip.setStyleSheet(f"background: {color}; border-radius: 2px;")
        layout.addWidget(strip)


class AccountsWidget(QWidget):
    def __init__(self, db, user_id: int):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        title = QLabel("Minhas Contas")
        title.setObjectName("title-label")
        btn_add = QPushButton("+ Nova Conta")
        btn_add.setObjectName("btn-success")
        btn_add.clicked.connect(self._add_account)
        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        root_layout.addLayout(toolbar)

        # Summary strip
        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("card")
        sum_lay = QHBoxLayout(self.summary_frame)
        sum_lay.setContentsMargins(16, 12, 16, 12)
        self.lbl_total = QLabel("Saldo Total: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        self.lbl_count = QLabel("0 contas")
        self.lbl_count.setStyleSheet("font-size: 13px; color: #94A3B8;")
        sum_lay.addWidget(self.lbl_total)
        sum_lay.addStretch()
        sum_lay.addWidget(self.lbl_count)
        root_layout.addWidget(self.summary_frame)

        # Scrollable grid of cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_container)
        root_layout.addWidget(scroll, 1)

    # ── Refresh ────────────────────────────────────────────────────────────────
    def refresh(self):
        accounts = self.db.get_accounts(self.user_id)
        total = sum(a["balance"] for a in accounts)
        bal_color = "#059669" if total >= 0 else "#DC2626"
        self.lbl_total.setText(f"Saldo Total: {_fmt_brl(total)}")
        self.lbl_total.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {bal_color};")
        self.lbl_count.setText(f"{len(accounts)} conta{'s' if len(accounts) != 1 else ''}")

        # Clear grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not accounts:
            empty = QLabel("Nenhuma conta cadastrada.\nClique em '+ Nova Conta' para começar.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 14px;")
            self.grid.addWidget(empty, 0, 0)
            return

        cols = 3
        for i, acct in enumerate(accounts):
            a = dict(acct)
            row, col = divmod(i, cols)
            card = AccountCard(
                a,
                on_edit=lambda checked=False, ac=a: self._edit_account(ac),
                on_delete=lambda checked=False, ac=a: self._delete_account(ac),
            )
            self.grid.addWidget(card, row, col)

    # ── CRUD ───────────────────────────────────────────────────────────────────
    def _add_account(self):
        dlg = AccountDialog(self.db, self.user_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_account(self, account: dict):
        dlg = AccountDialog(self.db, self.user_id, account=account, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_account(self, account: dict):
        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir a conta \"{account['name']}\"?\n\nAs transações vinculadas não serão excluídas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_account(account["id"]):
                self.refresh()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a conta.")
