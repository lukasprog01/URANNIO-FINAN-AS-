from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDialog, QLineEdit, QComboBox, QFormLayout, QDialogButtonBox,
    QMessageBox, QScrollArea, QSizePolicy, QTabWidget, QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QIcon


COLOR_OPTIONS = [
    ("#10B981", "Verde"),
    ("#3B82F6", "Azul"),
    ("#8B5CF6", "Roxo"),
    ("#F97316", "Laranja"),
    ("#EF4444", "Vermelho"),
    ("#F59E0B", "Amarelo"),
    ("#EC4899", "Rosa"),
    ("#06B6D4", "Ciano"),
    ("#6B7280", "Cinza"),
    ("#0F172A", "Preto"),
]

ICONS = [
    "💰","💵","💸","💳","🏦","📈","📉","💼","💻","🏠","🚗","🍔","🍕","☕",
    "🛒","💊","🏋️","📚","🎭","✈️","🎮","👕","🏥","🎓","🎵","📱","⚡","🌱",
    "🐾","🎁","🔧","🏗️","🚀","⭐","🌍","🎯","🛡️","📦","🏧","💹",
]


class CategoryDialog(QDialog):
    def __init__(self, db, user_id: int, category: dict = None, default_type: str = "expense", parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.category = category
        self.setWindowTitle("Nova Categoria" if not category else "Editar Categoria")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui(default_type)
        if category:
            self._populate(category)

    def _build_ui(self, default_type):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: Alimentação, Salário...")
        form.addRow("Nome *", self.name_input)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItem("💰 Receita", "income")
        self.type_combo.addItem("💸 Despesa", "expense")
        if default_type == "income":
            self.type_combo.setCurrentIndex(0)
        else:
            self.type_combo.setCurrentIndex(1)
        form.addRow("Tipo *", self.type_combo)

        # Icon
        self.icon_combo = QComboBox()
        for ico in ICONS:
            self.icon_combo.addItem(ico, ico)
        form.addRow("Ícone", self.icon_combo)

        # Color
        self.color_combo = QComboBox()
        for hex_color, name in COLOR_OPTIONS:
            self.color_combo.addItem(f"  ● {name}", hex_color)
        form.addRow("Cor", self.color_combo)

        layout.addLayout(form)

        # Preview
        self.preview = QLabel("💰  Nova Categoria")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(50)
        self.preview.setStyleSheet(
            "background: #EFF6FF; border-radius: 8px; font-size: 15px; font-weight: 600; color: #1E40AF;"
        )
        layout.addWidget(self.preview)

        self.icon_combo.currentIndexChanged.connect(self._update_preview)
        self.name_input.textChanged.connect(self._update_preview)
        self.color_combo.currentIndexChanged.connect(self._update_preview)

        btns = QDialogButtonBox()
        btn_save = btns.addButton("Salvar", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_save.setDefault(True)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _update_preview(self):
        icon = self.icon_combo.currentData() or "💰"
        name = self.name_input.text().strip() or "Nova Categoria"
        color = self.color_combo.currentData() or "#3B82F6"
        self.preview.setText(f"{icon}  {name}")
        self.preview.setStyleSheet(
            f"background: {color}22; border-radius: 8px; font-size: 15px; "
            f"font-weight: 600; color: {color};"
        )

    def _populate(self, c: dict):
        self.name_input.setText(c["name"])
        idx = self.type_combo.findData(c["type"])
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        idx = self.icon_combo.findData(c.get("icon", "💰"))
        if idx >= 0:
            self.icon_combo.setCurrentIndex(idx)
        idx = self.color_combo.findData(c.get("color", "#3B82F6"))
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        self._update_preview()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Atenção", "O nome da categoria é obrigatório.")
            return

        cat_type = self.type_combo.currentData()
        icon = self.icon_combo.currentData()
        color = self.color_combo.currentData()

        if self.category:
            ok = self.db.update_category(self.category["id"], name, cat_type, color, icon)
        else:
            ok = self.db.create_category(self.user_id, name, cat_type, color, icon)

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar a categoria.")


class CategoryRow(QFrame):
    def __init__(self, category: dict, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(56)
        self._build(category, on_edit, on_delete)

    def _build(self, c, on_edit, on_delete):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 12, 8)
        layout.setSpacing(12)

        color = c.get("color") or "#3B82F6"
        icon = c.get("icon") or "💰"

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background: {color}22; border-radius: 18px; font-size: 18px;"
        )

        name_lbl = QLabel(c["name"])
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 10px;")

        btn_edit = QPushButton("✏️")
        btn_edit.setObjectName("btn-icon")
        btn_edit.setFixedSize(30, 30)
        btn_edit.setToolTip("Editar")
        btn_edit.clicked.connect(on_edit)

        btn_del = QPushButton("🗑️")
        btn_del.setObjectName("btn-icon")
        btn_del.setFixedSize(30, 30)
        btn_del.setToolTip("Excluir")
        btn_del.clicked.connect(on_delete)

        layout.addWidget(icon_lbl)
        layout.addWidget(dot)
        layout.addWidget(name_lbl)
        layout.addStretch()
        layout.addWidget(btn_edit)
        layout.addWidget(btn_del)


class CategoriesWidget(QWidget):
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
        title = QLabel("Categorias")
        title.setObjectName("title-label")
        btn_income = QPushButton("+ Receita")
        btn_income.setObjectName("btn-success")
        btn_income.clicked.connect(lambda: self._add_category("income"))
        btn_expense = QPushButton("+ Despesa")
        btn_expense.setObjectName("btn-danger")
        btn_expense.clicked.connect(lambda: self._add_category("expense"))
        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(btn_income)
        toolbar.addWidget(btn_expense)
        root.addLayout(toolbar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { padding: 10px 24px; font-size: 13px; font-weight: 500; }
            QTabBar::tab:selected { color: #3B82F6; border-bottom: 2px solid #3B82F6; }
        """)

        # Income tab
        self.income_scroll = QScrollArea()
        self.income_scroll.setWidgetResizable(True)
        self.income_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.income_scroll.setStyleSheet("background: transparent;")
        self.income_container = QWidget()
        self.income_container.setStyleSheet("background: transparent;")
        self.income_layout = QVBoxLayout(self.income_container)
        self.income_layout.setContentsMargins(0, 8, 0, 8)
        self.income_layout.setSpacing(8)
        self.income_layout.addStretch()
        self.income_scroll.setWidget(self.income_container)

        # Expense tab
        self.expense_scroll = QScrollArea()
        self.expense_scroll.setWidgetResizable(True)
        self.expense_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.expense_scroll.setStyleSheet("background: transparent;")
        self.expense_container = QWidget()
        self.expense_container.setStyleSheet("background: transparent;")
        self.expense_layout = QVBoxLayout(self.expense_container)
        self.expense_layout.setContentsMargins(0, 8, 0, 8)
        self.expense_layout.setSpacing(8)
        self.expense_layout.addStretch()
        self.expense_scroll.setWidget(self.expense_container)

        self.tabs.addTab(self.income_scroll, "💰  Receitas")
        self.tabs.addTab(self.expense_scroll, "💸  Despesas")
        root.addWidget(self.tabs)

    def refresh(self):
        self._refresh_list(
            self.income_layout,
            self.db.get_categories(self.user_id, "income"),
            "income",
        )
        self._refresh_list(
            self.expense_layout,
            self.db.get_categories(self.user_id, "expense"),
            "expense",
        )

    def _refresh_list(self, layout: QVBoxLayout, categories: list, cat_type: str):
        # Remove all but the trailing stretch
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not categories:
            empty = QLabel(f"Nenhuma categoria de {'receita' if cat_type == 'income' else 'despesa'} cadastrada.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 14px; padding: 20px;")
            layout.insertWidget(0, empty)
            return

        for i, cat in enumerate(categories):
            c = dict(cat)
            row = CategoryRow(
                c,
                on_edit=lambda checked=False, cc=c: self._edit_category(cc),
                on_delete=lambda checked=False, cc=c: self._delete_category(cc),
            )
            layout.insertWidget(i, row)

    # ── CRUD ───────────────────────────────────────────────────────────────────
    def _add_category(self, default_type: str):
        dlg = CategoryDialog(self.db, self.user_id, default_type=default_type, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_category(self, category: dict):
        dlg = CategoryDialog(self.db, self.user_id, category=category, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_category(self, category: dict):
        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir a categoria \"{category['name']}\"?\n\n"
            "Transações vinculadas a esta categoria perderão a referência.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_category(category["id"]):
                self.refresh()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a categoria.")
