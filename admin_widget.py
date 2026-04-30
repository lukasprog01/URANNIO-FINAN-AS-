import secrets
import string
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QLineEdit, QApplication,
)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor


def _gen_temp_password(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


class _EmailWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, em, to_email: str, username: str, temp_pwd: str):
        super().__init__()
        self.em = em
        self.to_email = to_email
        self.username = username
        self.temp_pwd = temp_pwd

    def run(self):
        result = self.em.send_temp_password(self.to_email, self.username, self.temp_pwd)
        self.done.emit(result["success"], result.get("error", ""))


class AdminWidget(QWidget):
    def __init__(self, db, current_user_id: int, cfg, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_user_id = current_user_id
        self.cfg = cfg
        self._email_workers: list[_EmailWorker] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Stats bar ──────────────────────────────────────────────────────
        stats_card = QFrame()
        stats_card.setObjectName("card")
        stats_lay = QHBoxLayout(stats_card)
        stats_lay.setContentsMargins(20, 14, 20, 14)
        stats_lay.setSpacing(0)

        self.lbl_count = QLabel("— usuários")
        self.lbl_count.setStyleSheet("font-size: 13px; color: #64748B;")

        btn_refresh = QPushButton("🔄  Atualizar")
        btn_refresh.setObjectName("btn-secondary")
        btn_refresh.setFixedHeight(32)
        btn_refresh.clicked.connect(self.refresh)

        stats_lay.addWidget(self.lbl_count)
        stats_lay.addStretch()
        stats_lay.addWidget(btn_refresh)
        root.addWidget(stats_card)

        # ── Search ─────────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        self.search_inp = QLineEdit()
        self.search_inp.setPlaceholderText("🔍  Buscar por nome ou e-mail...")
        self.search_inp.setMinimumHeight(36)
        self.search_inp.textChanged.connect(self._filter_table)
        search_row.addWidget(self.search_inp)
        root.addLayout(search_row)

        # ── Table ──────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "Usuário", "E-mail", "Perfil", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 260)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: white; border: 1px solid #E2E8F0;
                border-radius: 10px; gridline-color: #F1F5F9;
                font-size: 13px;
            }
            QTableWidget::item { padding: 8px 10px; color: #1E293B; }
            QTableWidget::item:selected { background: #EFF6FF; color: #1E40AF; }
            QHeaderView::section {
                background: #F8FAFC; color: #64748B; font-weight: 700;
                font-size: 11px; border: none; border-bottom: 1px solid #E2E8F0;
                padding: 10px; letter-spacing: 0.5px;
            }
            QTableWidget::item:alternate { background: #FAFCFF; }
        """)
        self.table.setMinimumHeight(300)
        root.addWidget(self.table, 1)

        self._all_users: list[dict] = []

    def refresh(self):
        self._all_users = self.db.get_all_users()
        total = len(self._all_users)
        admins = sum(1 for u in self._all_users if u.get("role") == "admin")
        self.lbl_count.setText(
            f"{total} usuário{'s' if total != 1 else ''}  ·  {admins} administrador{'es' if admins != 1 else ''}"
        )
        self._populate(self._all_users)

    def _filter_table(self, text: str):
        q = text.lower()
        filtered = [u for u in self._all_users
                    if q in u["username"].lower() or q in u["email"].lower()]
        self._populate(filtered)

    def _populate(self, users: list[dict]):
        self.table.setRowCount(len(users))
        self.table.setRowHeight
        for row, user in enumerate(users):
            self.table.setRowHeight(row, 52)
            is_self = user["id"] == self.current_user_id
            is_admin = user.get("role") == "admin"

            # # ID
            id_item = QTableWidgetItem(str(user["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setForeground(QColor("#94A3B8"))
            self.table.setItem(row, 0, id_item)

            # Usuário
            icon = "👑" if is_admin else "👤"
            suffix = "  (você)" if is_self else ""
            self.table.setItem(row, 1, QTableWidgetItem(f"{icon}  {user['username']}{suffix}"))

            # E-mail
            self.table.setItem(row, 2, QTableWidgetItem(user["email"]))

            # Perfil badge
            role_item = QTableWidgetItem("Administrador" if is_admin else "Usuário")
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            role_item.setForeground(QColor("#059669" if is_admin else "#3B82F6"))
            self.table.setItem(row, 3, role_item)

            # Ações
            self.table.setCellWidget(row, 4, self._make_actions(user, is_self, is_admin))

    def _make_actions(self, user: dict, is_self: bool, is_admin: bool) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(5)

        # Reset password
        btn_pwd = QPushButton("🔑 Senha")
        btn_pwd.setFixedHeight(28)
        btn_pwd.setStyleSheet(
            "QPushButton { background:#EFF6FF; color:#3B82F6; border:1px solid #BFDBFE; "
            "border-radius:6px; font-size:11px; font-weight:600; padding:0 8px; }"
            "QPushButton:hover { background:#DBEAFE; }"
        )
        btn_pwd.clicked.connect(lambda _, u=user: self._reset_password(u))
        lay.addWidget(btn_pwd)

        if not is_self:
            # Toggle role
            next_role = "user" if is_admin else "admin"
            role_label = "👤 Rebaixar" if is_admin else "👑 Admin"
            btn_role = QPushButton(role_label)
            btn_role.setFixedHeight(28)
            btn_role.setStyleSheet(
                "QPushButton { background:#F0FDF4; color:#059669; border:1px solid #A7F3D0; "
                "border-radius:6px; font-size:11px; font-weight:600; padding:0 8px; }"
                "QPushButton:hover { background:#DCFCE7; }"
            )
            btn_role.clicked.connect(lambda _, u=user, r=next_role: self._set_role(u, r))
            lay.addWidget(btn_role)

            # Delete
            btn_del = QPushButton("🗑️")
            btn_del.setFixedHeight(28)
            btn_del.setFixedWidth(32)
            btn_del.setStyleSheet(
                "QPushButton { background:#FEF2F2; color:#DC2626; border:1px solid #FECACA; "
                "border-radius:6px; font-size:12px; }"
                "QPushButton:hover { background:#FEE2E2; }"
            )
            btn_del.clicked.connect(lambda _, u=user: self._delete_user(u))
            lay.addWidget(btn_del)

        lay.addStretch()
        return w

    # ── Actions ────────────────────────────────────────────────────────────────

    def _reset_password(self, user: dict):
        temp_pwd = _gen_temp_password()
        if not self.db.set_temp_password(user["id"], temp_pwd):
            QMessageBox.critical(self, "Erro", "Não foi possível gerar a senha temporária.")
            return

        # Try to send email if configured
        if self.cfg.email_sender and self.cfg.email_smtp_host:
            self._send_email_async(user, temp_pwd)
        else:
            self._show_temp_password_dialog(user["username"], user["email"], temp_pwd)

    def _send_email_async(self, user: dict, temp_pwd: str):
        from email_manager import EmailManager
        em = EmailManager(
            self.cfg.email_smtp_host, self.cfg.email_smtp_port,
            self.cfg.email_sender, self.cfg.email_password, self.cfg.email_use_tls,
        )
        worker = _EmailWorker(em, user["email"], user["username"], temp_pwd)

        def on_done(ok: bool, error: str):
            if ok:
                QMessageBox.information(
                    self, "Senha Enviada",
                    f"✅  Senha temporária enviada para {user['email']}.\n\n"
                    f"O usuário deverá usar essa senha no próximo login\n"
                    f"e definir uma nova senha permanente."
                )
            else:
                # Email failed — show password manually
                self._show_temp_password_dialog(
                    user["username"], user["email"], temp_pwd,
                    email_error=error
                )
            self._email_workers.remove(worker)

        worker.done.connect(on_done)
        worker.finished.connect(worker.deleteLater)
        self._email_workers.append(worker)
        worker.start()

    def _show_temp_password_dialog(self, username: str, email: str,
                                   temp_pwd: str, *, email_error: str = ""):
        dlg = QDialog(self)
        dlg.setWindowTitle("Senha Temporária Gerada")
        dlg.setMinimumWidth(440)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        if email_error:
            err_frame = QFrame()
            err_frame.setStyleSheet(
                "QFrame{background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;}"
            )
            el = QVBoxLayout(err_frame)
            el.setContentsMargins(12, 10, 12, 10)
            el.addWidget(QLabel(f"⚠️  E-mail não enviado: {email_error[:80]}"))
            lay.addWidget(err_frame)

        info = QLabel(
            f"Senha temporária criada para <b>{username}</b> ({email}).\n"
            "Entregue esta senha ao usuário pessoalmente ou por outro meio seguro."
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 13px; color: #374151;")
        lay.addWidget(info)

        pwd_frame = QFrame()
        pwd_frame.setStyleSheet(
            "QFrame{background:#F0FDF4;border:2px solid #10B981;border-radius:10px;}"
        )
        pl = QVBoxLayout(pwd_frame)
        pl.setContentsMargins(16, 14, 16, 14)
        lbl_hint = QLabel("SENHA TEMPORÁRIA (válida por 24h)")
        lbl_hint.setStyleSheet("font-size:10px;font-weight:700;color:#065F46;letter-spacing:1px;")
        lbl_pwd = QLabel(temp_pwd)
        lbl_pwd.setStyleSheet("font-size:24px;font-weight:800;color:#059669;letter-spacing:4px;")
        lbl_pwd.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        btn_copy = QPushButton("📋  Copiar Senha")
        btn_copy.setStyleSheet(
            "QPushButton { background:#D1FAE5; color:#065F46; border:1px solid #6EE7B7; "
            "border-radius:6px; font-size:12px; font-weight:600; padding:4px 12px; }"
            "QPushButton:hover { background:#A7F3D0; }"
        )
        btn_copy.setMinimumHeight(30)
        def _copy():
            QApplication.clipboard().setText(temp_pwd)
            btn_copy.setText("✓  Copiado!")
            QTimer.singleShot(2000, lambda: btn_copy.setText("📋  Copiar Senha"))
        btn_copy.clicked.connect(_copy)
        pl.addWidget(lbl_hint)
        pl.addWidget(lbl_pwd)
        pl.addWidget(btn_copy)
        lay.addWidget(pwd_frame)

        note = QLabel("O usuário precisará alterar a senha no próximo login.")
        note.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lay.addWidget(note)

        btn_ok = QPushButton("Fechar")
        btn_ok.setObjectName("btn-success")
        btn_ok.setMinimumHeight(36)
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)

        dlg.exec()

    def _set_role(self, user: dict, new_role: str):
        if new_role == "user":
            # Prevent demoting if only one admin
            admins = [u for u in self._all_users if u.get("role") == "admin"]
            if len(admins) <= 1:
                QMessageBox.warning(
                    self, "Atenção",
                    "Não é possível remover o último administrador do sistema."
                )
                return
            verb = "remover os privilégios de administrador"
        else:
            verb = "tornar administrador"

        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja {verb} de {user['username']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.set_user_role(user["id"], new_role):
                self.refresh()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível alterar o perfil.")

    def _delete_user(self, user: dict):
        reply = QMessageBox.question(
            self, "Excluir Usuário",
            f"Excluir permanentemente o usuário <b>{user['username']}</b>?<br>"
            "Todas as suas transações, contas e dados serão removidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_user_admin(user["id"]):
                self.refresh()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir o usuário.")
