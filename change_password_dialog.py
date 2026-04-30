from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from styles import MAIN_STYLE


class ChangePasswordDialog(QDialog):
    """Dialog shown when a user needs to set a new password (temp password or voluntary)."""

    def __init__(self, db, user_id: int, is_temp: bool = False, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.is_temp = is_temp
        self.setWindowTitle("Alterar Senha — URANNIO")
        self.setMinimumWidth(420)
        self.setFixedWidth(420)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Header
        title = QLabel("🔐  Nova Senha")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        if self.is_temp:
            banner = QFrame()
            banner.setStyleSheet(
                "QFrame { background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 8px; }"
            )
            bl = QVBoxLayout(banner)
            bl.setContentsMargins(14, 12, 14, 12)
            msg = QLabel(
                "⚠️  Você está usando uma senha temporária.\n"
                "Defina uma nova senha permanente para continuar."
            )
            msg.setStyleSheet("font-size: 13px; color: #9A3412;")
            msg.setWordWrap(True)
            bl.addWidget(msg)
            layout.addWidget(banner)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #E2E8F0; max-height: 1px; border: none;")
        layout.addWidget(sep)

        lbl_new = QLabel("Nova Senha")
        lbl_new.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.inp_new = QLineEdit()
        self.inp_new.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_new.setPlaceholderText("Mínimo 6 caracteres")
        self.inp_new.setMinimumHeight(38)
        self.inp_new.returnPressed.connect(self._save)

        lbl_confirm = QLabel("Confirmar Nova Senha")
        lbl_confirm.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.inp_confirm = QLineEdit()
        self.inp_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_confirm.setPlaceholderText("Repita a nova senha")
        self.inp_confirm.setMinimumHeight(38)
        self.inp_confirm.returnPressed.connect(self._save)

        self.lbl_error = QLabel()
        self.lbl_error.setStyleSheet(
            "color: #EF4444; font-size: 12px; background: #FEF2F2; "
            "border: 1px solid #FECACA; border-radius: 6px; padding: 6px 10px;"
        )
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        layout.addWidget(lbl_new)
        layout.addWidget(self.inp_new)
        layout.addSpacing(4)
        layout.addWidget(lbl_confirm)
        layout.addWidget(self.inp_confirm)
        layout.addWidget(self.lbl_error)

        layout.addSpacing(6)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if not self.is_temp:
            btn_cancel = QPushButton("Cancelar")
            btn_cancel.setObjectName("btn-secondary")
            btn_cancel.setMinimumHeight(38)
            btn_cancel.clicked.connect(self.reject)
            btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("✓  Salvar Nova Senha")
        btn_save.setObjectName("btn-success")
        btn_save.setMinimumHeight(38)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save, 1)
        layout.addLayout(btn_row)

    def _save(self):
        new_pwd = self.inp_new.text()
        confirm = self.inp_confirm.text()
        if len(new_pwd) < 6:
            self._err("A senha deve ter ao menos 6 caracteres.")
            return
        if new_pwd != confirm:
            self._err("As senhas não coincidem.")
            return
        if self.db.change_password(self.user_id, new_pwd):
            self.accept()
        else:
            self._err("Erro ao salvar. Tente novamente.")

    def _err(self, msg: str):
        self.lbl_error.setText(f"✕  {msg}")
        self.lbl_error.show()
