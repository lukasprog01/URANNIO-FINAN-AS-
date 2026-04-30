import secrets
import string
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QStackedWidget, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from styles import LOGIN_STYLE
from animated_logo import AnimatedLogo
from change_password_dialog import ChangePasswordDialog


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
        r = self.em.send_temp_password(self.to_email, self.username, self.temp_pwd)
        self.done.emit(r["success"], r.get("error", ""))


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(dict)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.first_run = (db.get_user_count() == 0)
        self._email_worker = None

        self.setWindowTitle("URANNIO — Login")
        self.setMinimumSize(960, 620)
        self.resize(1000, 680)
        self.setStyleSheet(LOGIN_STYLE)
        self._build_ui()
        self._center_window()

        if self.first_run:
            self.stack.setCurrentIndex(1)   # go straight to register

    def _center_window(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("login-root")
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left panel (branding) ──────────────────────────────────────────
        left = QWidget()
        left.setObjectName("login-root")
        left.setMinimumWidth(380)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(50, 60, 50, 60)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = AnimatedLogo(size=88)
        icon_lbl.setStyleSheet("background: transparent;")

        name_lbl = QLabel("URANNIO")
        name_lbl.setObjectName("app-name")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tag_lbl = QLabel("Gerencie suas finanças com\nintelligência e simplicidade")
        tag_lbl.setObjectName("app-tagline")
        tag_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_lbl.setWordWrap(True)

        left_layout.addStretch()
        left_layout.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        left_layout.addSpacing(8)
        left_layout.addWidget(name_lbl)
        left_layout.addSpacing(8)
        left_layout.addWidget(tag_lbl)
        left_layout.addSpacing(40)

        features = [
            ("📊", "Dashboard completo em tempo real"),
            ("💳", "Controle de múltiplas contas"),
            ("📈", "Relatórios e gráficos detalhados"),
            ("🎯", "Orçamento por categorias"),
        ]
        for icon, text in features:
            row = QHBoxLayout()
            ico = QLabel(icon)
            ico.setFixedWidth(28)
            ico.setStyleSheet("font-size: 18px;")
            txt = QLabel(text)
            txt.setStyleSheet("color: #64748B; font-size: 13px;")
            row.addWidget(ico)
            row.addWidget(txt)
            row.addStretch()
            left_layout.addLayout(row)
            left_layout.addSpacing(8)

        left_layout.addStretch()

        # ── Right panel (form card) ────────────────────────────────────────
        right = QWidget()
        right.setObjectName("login-root")
        right_layout = QHBoxLayout(right)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setObjectName("login-card")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(0)

        # Stack: 0=login, 1=register, 2=forgot
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_form())
        self.stack.addWidget(self._build_register_form())
        self.stack.addWidget(self._build_forgot_form())

        card_layout.addWidget(self.stack)
        right_layout.addWidget(card)

        main_layout.addWidget(left, 4)
        main_layout.addWidget(right, 5)

    # ── Login form ─────────────────────────────────────────────────────────────
    def _build_login_form(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Bem-vindo de volta!")
        title.setObjectName("form-title")
        sub = QLabel("Entre na sua conta para continuar")
        sub.setObjectName("form-subtitle")

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(sub)
        layout.addSpacing(28)

        self.login_error = QLabel()
        self.login_error.setObjectName("error-label")
        self.login_error.hide()
        self.login_error.setWordWrap(True)

        layout.addWidget(self.login_error)
        layout.addSpacing(4)

        lbl_user = QLabel("Usuário ou E-mail")
        lbl_user.setObjectName("field-label")
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Digite seu usuário ou e-mail")

        layout.addWidget(lbl_user)
        layout.addSpacing(6)
        layout.addWidget(self.login_username)
        layout.addSpacing(16)

        lbl_pass = QLabel("Senha")
        lbl_pass.setObjectName("field-label")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Digite sua senha")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(lbl_pass)
        layout.addSpacing(6)
        layout.addWidget(self.login_password)
        layout.addSpacing(20)

        self.remember_me = QCheckBox("Lembrar-me")
        layout.addWidget(self.remember_me)
        layout.addSpacing(20)

        btn_login = QPushButton("  Entrar")
        btn_login.setObjectName("btn-login")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self._do_login)
        self.login_username.returnPressed.connect(self._do_login)
        self.login_password.returnPressed.connect(self._do_login)

        layout.addWidget(btn_login)
        layout.addSpacing(14)

        # Forgot password link
        row_forgot = QHBoxLayout()
        btn_forgot = QPushButton("Esqueceu sua senha?")
        btn_forgot.setObjectName("btn-link")
        btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_forgot.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        row_forgot.addStretch()
        row_forgot.addWidget(btn_forgot)
        row_forgot.addStretch()
        layout.addLayout(row_forgot)
        layout.addSpacing(10)

        row = QHBoxLayout()
        lbl_no_acct = QLabel("Não tem uma conta?")
        lbl_no_acct.setStyleSheet("color: #64748B; font-size: 13px;")
        btn_reg = QPushButton("Cadastre-se")
        btn_reg.setObjectName("btn-link")
        btn_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reg.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        row.addStretch()
        row.addWidget(lbl_no_acct)
        row.addSpacing(4)
        row.addWidget(btn_reg)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

        return w

    # ── Register form ──────────────────────────────────────────────────────────
    def _build_register_form(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Criar conta")
        title.setObjectName("form-title")
        sub = QLabel("Preencha os campos para se cadastrar")
        sub.setObjectName("form-subtitle")

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(sub)
        layout.addSpacing(12)

        # Admin first-run banner
        if self.first_run:
            banner = QFrame()
            banner.setStyleSheet(
                "QFrame { background: #F0FDF4; border: 1px solid #A7F3D0; border-radius: 8px; }"
            )
            bl = QVBoxLayout(banner)
            bl.setContentsMargins(12, 10, 12, 10)
            btext = QLabel(
                "👑  Primeiro acesso — você será registrado como\n"
                "Administrador do sistema."
            )
            btext.setStyleSheet("font-size: 12px; color: #065F46; font-weight: 600;")
            btext.setWordWrap(True)
            bl.addWidget(btext)
            layout.addWidget(banner)
            layout.addSpacing(10)

        self.reg_error = QLabel()
        self.reg_error.setObjectName("error-label")
        self.reg_error.hide()
        self.reg_error.setWordWrap(True)

        self.reg_success = QLabel()
        self.reg_success.setObjectName("success-label")
        self.reg_success.hide()
        self.reg_success.setWordWrap(True)

        layout.addWidget(self.reg_error)
        layout.addWidget(self.reg_success)
        layout.addSpacing(4)

        fields = [
            ("Nome de usuário", "reg_username", "Escolha um nome de usuário", False),
            ("E-mail",          "reg_email",    "seu@email.com",              False),
            ("Senha",           "reg_password", "Mínimo 6 caracteres",        True),
            ("Confirmar senha", "reg_confirm",  "Repita a senha",             True),
        ]

        for label, attr, placeholder, is_pass in fields:
            lbl = QLabel(label)
            lbl.setObjectName("field-label")
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            if is_pass:
                inp.setEchoMode(QLineEdit.EchoMode.Password)
            setattr(self, attr, inp)
            layout.addWidget(lbl)
            layout.addSpacing(5)
            layout.addWidget(inp)
            layout.addSpacing(12)

        layout.addSpacing(4)

        btn_reg = QPushButton("  Criar Conta")
        btn_reg.setObjectName("btn-login")
        btn_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reg.clicked.connect(self._do_register)

        layout.addWidget(btn_reg)
        layout.addSpacing(16)

        row = QHBoxLayout()
        lbl_has = QLabel("Já tem uma conta?")
        lbl_has.setStyleSheet("color: #64748B; font-size: 13px;")
        btn_login = QPushButton("Entrar")
        btn_login.setObjectName("btn-link")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        row.addStretch()
        row.addWidget(lbl_has)
        row.addSpacing(4)
        row.addWidget(btn_login)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

        return w

    # ── Forgot password form ───────────────────────────────────────────────────
    def _build_forgot_form(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Recuperar Senha")
        title.setObjectName("form-title")
        sub = QLabel("Informe seu e-mail para receber\numa senha temporária")
        sub.setObjectName("form-subtitle")
        sub.setWordWrap(True)

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(sub)
        layout.addSpacing(28)

        self.forgot_msg = QLabel()
        self.forgot_msg.setWordWrap(True)
        self.forgot_msg.hide()
        layout.addWidget(self.forgot_msg)
        layout.addSpacing(4)

        # Password display box (shown only when no email is configured or sending fails)
        self.forgot_pwd_frame = QFrame()
        self.forgot_pwd_frame.setStyleSheet(
            "QFrame { background:#F0FDF4; border:2px solid #10B981; border-radius:10px; }"
        )
        fpf_lay = QVBoxLayout(self.forgot_pwd_frame)
        fpf_lay.setContentsMargins(16, 12, 16, 12)
        fpf_lay.setSpacing(6)
        fpf_hint = QLabel("SENHA TEMPORÁRIA (válida por 24h)")
        fpf_hint.setStyleSheet("font-size:10px; font-weight:700; color:#065F46; letter-spacing:1px;")
        self.forgot_pwd_lbl = QLabel()
        self.forgot_pwd_lbl.setStyleSheet(
            "font-size:22px; font-weight:800; color:#059669; letter-spacing:4px;"
        )
        self.forgot_pwd_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.btn_copy_forgot = QPushButton("📋  Copiar Senha")
        self.btn_copy_forgot.setStyleSheet(
            "QPushButton { background:#D1FAE5; color:#065F46; border:1px solid #6EE7B7; "
            "border-radius:6px; font-size:12px; font-weight:600; padding:4px 12px; }"
            "QPushButton:hover { background:#A7F3D0; }"
        )
        self.btn_copy_forgot.setMinimumHeight(30)
        self.btn_copy_forgot.clicked.connect(self._copy_forgot_pwd)
        fpf_lay.addWidget(fpf_hint)
        fpf_lay.addWidget(self.forgot_pwd_lbl)
        fpf_lay.addWidget(self.btn_copy_forgot)
        self.forgot_pwd_frame.hide()
        layout.addWidget(self.forgot_pwd_frame)
        layout.addSpacing(8)

        lbl_email = QLabel("E-mail cadastrado")
        lbl_email.setObjectName("field-label")
        self.forgot_email = QLineEdit()
        self.forgot_email.setPlaceholderText("seu@email.com")
        self.forgot_email.returnPressed.connect(self._do_forgot)

        layout.addWidget(lbl_email)
        layout.addSpacing(6)
        layout.addWidget(self.forgot_email)
        layout.addSpacing(20)

        self.btn_forgot_send = QPushButton("  Enviar Senha Temporária")
        self.btn_forgot_send.setObjectName("btn-login")
        self.btn_forgot_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_forgot_send.clicked.connect(self._do_forgot)
        layout.addWidget(self.btn_forgot_send)
        layout.addSpacing(16)

        row = QHBoxLayout()
        btn_back = QPushButton("← Voltar ao Login")
        btn_back.setObjectName("btn-link")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self._back_to_login)
        row.addStretch()
        row.addWidget(btn_back)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

        return w

    # ── Actions ────────────────────────────────────────────────────────────────
    def _do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            self._show_login_error("Preencha todos os campos.")
            return

        result = self.db.authenticate_user(username, password)
        if result["success"]:
            user = result["user"]
            self.login_error.hide()

            if user.get("must_change_password"):
                dlg = ChangePasswordDialog(self.db, user["id"], is_temp=True, parent=self)
                if dlg.exec() == dlg.DialogCode.Accepted:
                    user["must_change_password"] = 0
                    self.login_successful.emit(user)
                # else: stay on login
            else:
                self.login_successful.emit(user)
        else:
            self._show_login_error(result["error"])

    def _do_register(self):
        username = self.reg_username.text().strip()
        email    = self.reg_email.text().strip()
        password = self.reg_password.text()
        confirm  = self.reg_confirm.text()

        self.reg_error.hide()
        self.reg_success.hide()

        if not all([username, email, password, confirm]):
            self._show_reg_error("Preencha todos os campos.")
            return
        if len(username) < 3:
            self._show_reg_error("Nome de usuário deve ter ao menos 3 caracteres.")
            return
        if "@" not in email or "." not in email:
            self._show_reg_error("E-mail inválido.")
            return
        if len(password) < 6:
            self._show_reg_error("A senha deve ter ao menos 6 caracteres.")
            return
        if password != confirm:
            self._show_reg_error("As senhas não coincidem.")
            return

        result = self.db.create_user(username, email, password)
        if result["success"]:
            is_admin = result.get("role") == "admin"
            if self.first_run:
                # Primeiro acesso: entra no sistema automaticamente
                self.reg_success.setText("✓ Administrador criado! Entrando no sistema...")
                self.reg_success.show()
                auth = self.db.authenticate_user(username, password)
                if auth["success"]:
                    QTimer.singleShot(900, lambda: self.login_successful.emit(auth["user"]))
                else:
                    # Fallback: vai para login manual
                    QTimer.singleShot(900, lambda: self.stack.setCurrentIndex(0))
            else:
                suffix = " como Administrador" if is_admin else ""
                self.reg_success.setText(f"✓ Conta criada{suffix}! Redirecionando para o login...")
                self.reg_success.show()
                self.reg_username.clear()
                self.reg_email.clear()
                self.reg_password.clear()
                self.reg_confirm.clear()
                QTimer.singleShot(1500, lambda: self.stack.setCurrentIndex(0))
        else:
            self._show_reg_error(result["error"])

    def _do_forgot(self):
        email = self.forgot_email.text().strip()
        if not email or "@" not in email:
            self._show_forgot("E-mail inválido.", error=True)
            return

        user = self.db.get_user_by_email(email)
        if not user:
            self._show_forgot("E-mail não encontrado no sistema.", error=True)
            return

        temp_pwd = _gen_temp_password()
        if not self.db.set_temp_password(user["id"], temp_pwd):
            self._show_forgot("Erro ao gerar senha temporária. Tente novamente.", error=True)
            return

        # Try to send email
        from config_manager import ConfigManager
        cfg = ConfigManager()

        if cfg.email_sender and cfg.email_smtp_host:
            self.btn_forgot_send.setEnabled(False)
            self.btn_forgot_send.setText("Enviando...")
            self._send_forgot_email(cfg, user, temp_pwd)
        else:
            # Email not configured — show password directly with copy button
            self._show_forgot(
                "Senha temporária criada! Use-a no próximo login.\n"
                "Configure o e-mail nas Configurações para envio automático.",
                error=False,
            )
            self._show_forgot_pwd(temp_pwd)

    def _send_forgot_email(self, cfg, user: dict, temp_pwd: str):
        from email_manager import EmailManager
        em = EmailManager(
            cfg.email_smtp_host, cfg.email_smtp_port,
            cfg.email_sender, cfg.email_password, cfg.email_use_tls,
        )
        worker = _EmailWorker(em, user["email"], user["username"], temp_pwd)

        def on_done(ok: bool, error: str):
            self.btn_forgot_send.setEnabled(True)
            self.btn_forgot_send.setText("  Enviar Senha Temporária")
            if ok:
                self._show_forgot(
                    f"✓ Senha temporária enviada para {user['email']}.\n"
                    "Verifique sua caixa de entrada e faça login com ela.",
                    error=False,
                )
            else:
                self._show_forgot(
                    f"Não foi possível enviar o e-mail:\n{error[:80]}\n\n"
                    "Use a senha temporária abaixo no próximo login.",
                    error=True,
                )
                self._show_forgot_pwd(temp_pwd)
            self._email_worker = None

        worker.done.connect(on_done)
        worker.finished.connect(worker.deleteLater)
        self._email_worker = worker
        worker.start()

    def _back_to_login(self):
        self.forgot_msg.hide()
        self.forgot_pwd_frame.hide()
        self.forgot_email.clear()
        self.btn_forgot_send.setEnabled(True)
        self.btn_forgot_send.setText("  Enviar Senha Temporária")
        self.stack.setCurrentIndex(0)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _show_login_error(self, msg: str):
        self.login_error.setText(f"✕  {msg}")
        self.login_error.show()

    def _show_reg_error(self, msg: str):
        self.reg_error.setText(f"✕  {msg}")
        self.reg_error.show()

    def _show_forgot(self, msg: str, error: bool):
        style_err = (
            "color:#EF4444; font-size:12px; background:#FEF2F2; "
            "border:1px solid #FECACA; border-radius:6px; padding:8px 12px;"
        )
        style_ok = (
            "color:#059669; font-size:12px; background:#ECFDF5; "
            "border:1px solid #A7F3D0; border-radius:6px; padding:8px 12px;"
        )
        self.forgot_msg.setStyleSheet(style_err if error else style_ok)
        self.forgot_msg.setText(msg)
        self.forgot_msg.show()

    def _show_forgot_pwd(self, pwd: str):
        self._current_forgot_pwd = pwd
        self.forgot_pwd_lbl.setText(pwd)
        self.btn_copy_forgot.setText("📋  Copiar Senha")
        self.forgot_pwd_frame.show()

    def _copy_forgot_pwd(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._current_forgot_pwd)
        self.btn_copy_forgot.setText("✓  Copiado!")
        QTimer.singleShot(2000, lambda: self.btn_copy_forgot.setText("📋  Copiar Senha"))
