import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QCheckBox, QFileDialog, QMessageBox, QScrollArea,
    QTabWidget, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer


STATUS_STYLES = {
    "connected":    ("🟢", "Firebase Conectado",    "#ECFDF5", "#059669", "#A7F3D0"),
    "disconnected": ("🔴", "Firebase Desconectado", "#F8FAFC", "#64748B", "#E2E8F0"),
    "syncing":      ("🔄", "Sincronizando...",       "#EFF6FF", "#2563EB", "#BFDBFE"),
    "synced":       ("✅", "Dados Sincronizados",    "#ECFDF5", "#059669", "#A7F3D0"),
    "error":        ("⚠️", "Erro de Conexão",        "#FEF2F2", "#DC2626", "#FECACA"),
}

AI_MODELS = [
    ("claude-haiku-4-5-20251001", "Claude Haiku 4.5  —  rápido e econômico (recomendado)"),
    ("claude-sonnet-4-6",          "Claude Sonnet 4.6  —  mais detalhado e poderoso"),
    ("claude-opus-4-7",            "Claude Opus 4.7   —  máxima capacidade analítica"),
]


class SettingsWidget(QWidget):
    def __init__(self, db, user_id: int, firebase_manager, config_manager):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.fm = firebase_manager
        self.cfg = config_manager
        self._build_ui()
        self._connect_signals()
        self._restore_state()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_firebase_tab(), "🔥  Firebase")
        self.tabs.addTab(self._build_ai_tab(),       "🤖  Inteligência Artificial")
        self.tabs.addTab(self._build_email_tab(),    "📧  E-mail")
        root.addWidget(self.tabs)

    # ══════════════════════════════════════════════════════════════════════
    # FIREBASE TAB
    # ══════════════════════════════════════════════════════════════════════
    def _build_firebase_tab(self):
        outer, layout = self._make_scroll_tab()

        # ── Status card ────────────────────────────────────────────────
        self.fb_status_card = QFrame()
        self.fb_status_card.setObjectName("card")
        self.fb_status_card.setMinimumHeight(100)
        s_lay = QVBoxLayout(self.fb_status_card)
        s_lay.setContentsMargins(20, 16, 20, 16)
        s_lay.setSpacing(6)

        s_top = QHBoxLayout()
        self.fb_icon = QLabel("🔴")
        self.fb_icon.setStyleSheet("font-size: 32px;")
        self.fb_icon.setFixedWidth(48)
        s_text = QVBoxLayout()
        s_text.setSpacing(3)
        self.fb_title = QLabel("Firebase Desconectado")
        self.fb_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #64748B;")
        self.fb_msg = QLabel("Configure as credenciais abaixo para ativar a sincronização.")
        self.fb_msg.setStyleSheet("font-size: 12px; color: #94A3B8;")
        self.fb_msg.setWordWrap(True)
        s_text.addWidget(self.fb_title)
        s_text.addWidget(self.fb_msg)
        s_top.addWidget(self.fb_icon)
        s_top.addSpacing(10)
        s_top.addLayout(s_text, 1)
        self.fb_sync_time = QLabel("")
        self.fb_sync_time.setStyleSheet("font-size: 11px; color: #94A3B8;")
        s_lay.addLayout(s_top)
        s_lay.addWidget(self.fb_sync_time)
        layout.addWidget(self.fb_status_card)

        # ── Setup ──────────────────────────────────────────────────────
        setup = QFrame()
        setup.setObjectName("card")
        sl = QVBoxLayout(setup)
        sl.setContentsMargins(20, 16, 20, 16)
        sl.setSpacing(12)

        sl.addWidget(self._section_title("Configuração do Firebase"))

        lbl_cred = QLabel("Arquivo Service Account (JSON)")
        lbl_cred.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        sl.addWidget(lbl_cred)

        cred_row = QHBoxLayout()
        self.cred_path = QLineEdit()
        self.cred_path.setPlaceholderText("Selecione o arquivo service-account.json…")
        self.cred_path.setReadOnly(True)
        self.cred_path.setMinimumHeight(36)
        btn_browse = QPushButton("📂  Selecionar")
        btn_browse.setObjectName("btn-secondary")
        btn_browse.setMinimumWidth(130)
        btn_browse.clicked.connect(self._fb_browse)
        cred_row.addWidget(self.cred_path, 1)
        cred_row.addWidget(btn_browse)
        sl.addLayout(cred_row)

        hint = QLabel("Gerado em Firebase Console → Configurações → Contas de Serviço → Gerar nova chave.")
        hint.setStyleSheet("font-size: 11px; color: #94A3B8;")
        hint.setWordWrap(True)
        sl.addWidget(hint)

        btn_row = QHBoxLayout()
        self.fb_btn_connect = QPushButton("🔗  Conectar ao Firebase")
        self.fb_btn_connect.setObjectName("btn-success")
        self.fb_btn_connect.setMinimumHeight(38)
        self.fb_btn_connect.clicked.connect(self._fb_connect)
        self.fb_btn_disconnect = QPushButton("🔌  Desconectar")
        self.fb_btn_disconnect.setObjectName("btn-danger")
        self.fb_btn_disconnect.setMinimumHeight(38)
        self.fb_btn_disconnect.setVisible(False)
        self.fb_btn_disconnect.clicked.connect(self._fb_disconnect)
        btn_row.addWidget(self.fb_btn_connect)
        btn_row.addWidget(self.fb_btn_disconnect)
        btn_row.addStretch()
        sl.addLayout(btn_row)
        layout.addWidget(setup)

        # ── Sync options ───────────────────────────────────────────────
        opt = QFrame()
        opt.setObjectName("card")
        ol = QVBoxLayout(opt)
        ol.setContentsMargins(20, 16, 20, 16)
        ol.setSpacing(10)
        ol.addWidget(self._section_title("Opções de Sincronização"))

        self.fb_auto_check = QCheckBox("Sincronização automática em tempo real")
        self.fb_auto_check.setStyleSheet("font-size: 13px; color: #374151;")
        self.fb_auto_check.toggled.connect(self._fb_auto_toggled)
        ol.addWidget(self.fb_auto_check)

        auto_hint = QLabel(
            "Cada transação, conta ou categoria criada/alterada é enviada ao Firestore imediatamente."
        )
        auto_hint.setStyleSheet("font-size: 12px; color: #94A3B8;")
        auto_hint.setWordWrap(True)
        ol.addWidget(auto_hint)

        sync_row = QHBoxLayout()
        self.fb_btn_sync = QPushButton("🔄  Sincronizar Tudo Agora")
        self.fb_btn_sync.setMinimumHeight(36)
        self.fb_btn_sync.setEnabled(False)
        self.fb_btn_sync.clicked.connect(self._fb_sync_all)
        self.fb_sync_lbl = QLabel("")
        self.fb_sync_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        sync_row.addWidget(self.fb_btn_sync)
        sync_row.addSpacing(10)
        sync_row.addWidget(self.fb_sync_lbl)
        sync_row.addStretch()
        ol.addLayout(sync_row)
        layout.addWidget(opt)

        # ── Instructions ───────────────────────────────────────────────
        layout.addWidget(self._build_firebase_instructions())
        layout.addStretch()
        return outer

    def _build_firebase_instructions(self):
        steps = [
            ("1", "Acesse", "console.firebase.google.com", "https://console.firebase.google.com", "e crie um projeto."),
            ("2", "Ative o", "Firestore Database", None, "e escolha a região."),
            ("3", "Vá em", "Configurações → Contas de Serviço", None, "e clique em 'Gerar nova chave privada'."),
            ("4", "Salve o arquivo", ".json", None, "em local seguro no seu computador."),
            ("5", "Selecione o arquivo", "acima", None, "e clique em Conectar."),
        ]
        return self._build_steps_card("Como configurar o Firebase", steps, "#3B82F6")

    # ══════════════════════════════════════════════════════════════════════
    # AI TAB
    # ══════════════════════════════════════════════════════════════════════
    def _build_ai_tab(self):
        outer, layout = self._make_scroll_tab()

        # ── Status card ────────────────────────────────────────────────
        self.ai_status_card = QFrame()
        self.ai_status_card.setObjectName("card")
        self.ai_status_card.setMinimumHeight(90)
        as_lay = QHBoxLayout(self.ai_status_card)
        as_lay.setContentsMargins(20, 14, 20, 14)
        as_lay.setSpacing(12)

        self.ai_status_icon = QLabel("🔴")
        self.ai_status_icon.setStyleSheet("font-size: 28px;")
        self.ai_status_icon.setFixedWidth(40)

        ai_text = QVBoxLayout()
        ai_text.setSpacing(3)
        self.ai_status_title = QLabel("IA não configurada")
        self.ai_status_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #64748B;")
        self.ai_status_msg = QLabel("Insira sua chave da API Anthropic abaixo para ativar os insights de IA.")
        self.ai_status_msg.setStyleSheet("font-size: 12px; color: #94A3B8;")
        self.ai_status_msg.setWordWrap(True)
        ai_text.addWidget(self.ai_status_title)
        ai_text.addWidget(self.ai_status_msg)

        as_lay.addWidget(self.ai_status_icon)
        as_lay.addLayout(ai_text, 1)
        layout.addWidget(self.ai_status_card)

        # ── API Key ────────────────────────────────────────────────────
        key_card = QFrame()
        key_card.setObjectName("card")
        kl = QVBoxLayout(key_card)
        kl.setContentsMargins(20, 16, 20, 16)
        kl.setSpacing(12)
        kl.addWidget(self._section_title("Chave de API Anthropic"))

        lbl_key = QLabel("Chave da API (sk-ant-...)")
        lbl_key.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        kl.addWidget(lbl_key)

        key_row = QHBoxLayout()
        self.ai_key_input = QLineEdit()
        self.ai_key_input.setPlaceholderText("sk-ant-api03-...")
        self.ai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_key_input.setMinimumHeight(36)

        self.btn_show_key = QPushButton("👁")
        self.btn_show_key.setObjectName("btn-secondary")
        self.btn_show_key.setFixedSize(36, 36)
        self.btn_show_key.setCheckable(True)
        self.btn_show_key.toggled.connect(
            lambda c: self.ai_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if c else QLineEdit.EchoMode.Password
            )
        )
        key_row.addWidget(self.ai_key_input, 1)
        key_row.addWidget(self.btn_show_key)
        kl.addLayout(key_row)

        key_hint = QLabel(
            "Obtenha sua chave em: console.anthropic.com/settings/api-keys"
        )
        key_hint.setStyleSheet("font-size: 11px; color: #94A3B8;")
        kl.addWidget(key_hint)

        # Model selector
        lbl_model = QLabel("Modelo de IA")
        lbl_model.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        kl.addWidget(lbl_model)

        self.ai_model_combo = QComboBox()
        self.ai_model_combo.setMinimumHeight(36)
        for model_id, label in AI_MODELS:
            self.ai_model_combo.addItem(label, model_id)
        kl.addWidget(self.ai_model_combo)

        model_hint = QLabel(
            "Haiku é mais rápido e barato. Sonnet e Opus oferecem análises mais profundas."
        )
        model_hint.setStyleSheet("font-size: 11px; color: #94A3B8;")
        kl.addWidget(model_hint)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾  Salvar Configuração")
        btn_save.setObjectName("btn-success")
        btn_save.setMinimumHeight(38)
        btn_save.clicked.connect(self._ai_save)

        self.btn_test_ai = QPushButton("🔗  Testar Conexão")
        self.btn_test_ai.setObjectName("btn-secondary")
        self.btn_test_ai.setMinimumHeight(38)
        self.btn_test_ai.clicked.connect(self._ai_test)

        self.ai_test_lbl = QLabel("")
        self.ai_test_lbl.setStyleSheet("font-size: 12px; color: #64748B;")

        btn_row.addWidget(btn_save)
        btn_row.addWidget(self.btn_test_ai)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.ai_test_lbl)
        btn_row.addStretch()
        kl.addLayout(btn_row)
        layout.addWidget(key_card)

        # ── Privacy notice ─────────────────────────────────────────────
        privacy = QFrame()
        privacy.setStyleSheet(
            "QFrame { background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; }"
        )
        pl = QVBoxLayout(privacy)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(6)

        priv_title = QLabel("🔒  Privacidade e Segurança")
        priv_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #166534;")
        priv_text = QLabel(
            "• Seus dados financeiros são enviados diretamente para a API da Anthropic usando a sua própria chave.\n"
            "• A chave é armazenada apenas localmente neste computador (arquivo app_config.json).\n"
            "• Nunca compartilhamos suas informações com terceiros.\n"
            "• Os dados enviados incluem: resumo mensal, categorias de gastos e últimas 30 transações."
        )
        priv_text.setStyleSheet("font-size: 12px; color: #166534; line-height: 1.6;")
        priv_text.setWordWrap(True)
        pl.addWidget(priv_title)
        pl.addWidget(priv_text)
        layout.addWidget(privacy)

        # ── Instructions ───────────────────────────────────────────────
        layout.addWidget(self._build_ai_instructions())
        layout.addStretch()
        return outer

    def _build_ai_instructions(self):
        steps = [
            ("1", "Acesse", "console.anthropic.com", "https://console.anthropic.com", "e crie uma conta."),
            ("2", "Vá em", "API Keys", None, "no menu lateral."),
            ("3", "Clique em", "Create Key", None, "e dê um nome (ex: FinanceControl)."),
            ("4", "Copie a chave gerada", "(sk-ant-...)", None, "e cole no campo acima."),
            ("5", "Clique em", "Salvar Configuração", None, "e depois acesse o menu 🤖 IA Insights."),
        ]
        card = self._build_steps_card("Como obter a chave da API Anthropic", steps, "#7C3AED")
        lay = card.layout()

        cost_box = QFrame()
        cost_box.setStyleSheet(
            "QFrame { background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; }"
        )
        cl = QVBoxLayout(cost_box)
        cl.setContentsMargins(14, 10, 14, 10)
        cost_title = QLabel("💰  Custo estimado por análise")
        cost_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #1E40AF;")
        cost_text = QLabel(
            "Haiku 4.5: ~US$ 0,001 por análise  |  "
            "Sonnet 4.6: ~US$ 0,01 por análise  |  "
            "Opus 4.7: ~US$ 0,05 por análise"
        )
        cost_text.setStyleSheet("font-size: 12px; color: #1E40AF;")
        cost_text.setWordWrap(True)
        cl.addWidget(cost_title)
        cl.addWidget(cost_text)
        lay.addWidget(cost_box)
        return card

    # ══════════════════════════════════════════════════════════════════════
    # EMAIL TAB
    # ══════════════════════════════════════════════════════════════════════
    def _build_email_tab(self):
        outer, layout = self._make_scroll_tab()

        # ── Status card ────────────────────────────────────────────────
        self.email_status_card = QFrame()
        self.email_status_card.setObjectName("card")
        self.email_status_card.setMinimumHeight(90)
        es_lay = QHBoxLayout(self.email_status_card)
        es_lay.setContentsMargins(20, 14, 20, 14)
        es_lay.setSpacing(12)

        self.email_status_icon = QLabel("🔴")
        self.email_status_icon.setStyleSheet("font-size: 28px;")
        self.email_status_icon.setFixedWidth(40)

        em_text = QVBoxLayout()
        em_text.setSpacing(3)
        self.email_status_title = QLabel("E-mail não configurado")
        self.email_status_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #64748B;")
        self.email_status_msg = QLabel(
            "Configure o servidor SMTP para enviar senhas temporárias por e-mail."
        )
        self.email_status_msg.setStyleSheet("font-size: 12px; color: #94A3B8;")
        self.email_status_msg.setWordWrap(True)
        em_text.addWidget(self.email_status_title)
        em_text.addWidget(self.email_status_msg)

        es_lay.addWidget(self.email_status_icon)
        es_lay.addLayout(em_text, 1)
        layout.addWidget(self.email_status_card)

        # ── SMTP config card ───────────────────────────────────────────
        smtp_card = QFrame()
        smtp_card.setObjectName("card")
        sl = QVBoxLayout(smtp_card)
        sl.setContentsMargins(20, 16, 20, 16)
        sl.setSpacing(12)
        sl.addWidget(self._section_title("Configuração SMTP"))

        # Host + Port row
        host_port_row = QHBoxLayout()
        host_col = QVBoxLayout()
        lbl_host = QLabel("Servidor SMTP")
        lbl_host.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.email_host = QLineEdit()
        self.email_host.setPlaceholderText("smtp.gmail.com")
        self.email_host.setMinimumHeight(36)
        host_col.addWidget(lbl_host)
        host_col.addWidget(self.email_host)

        port_col = QVBoxLayout()
        lbl_port = QLabel("Porta")
        lbl_port.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.email_port = QLineEdit()
        self.email_port.setPlaceholderText("587")
        self.email_port.setMinimumHeight(36)
        self.email_port.setFixedWidth(80)
        port_col.addWidget(lbl_port)
        port_col.addWidget(self.email_port)

        host_port_row.addLayout(host_col, 1)
        host_port_row.addSpacing(10)
        host_port_row.addLayout(port_col)
        sl.addLayout(host_port_row)

        # Sender email
        lbl_sender = QLabel("E-mail do Remetente")
        lbl_sender.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.email_sender = QLineEdit()
        self.email_sender.setPlaceholderText("seu@gmail.com")
        self.email_sender.setMinimumHeight(36)
        sl.addWidget(lbl_sender)
        sl.addWidget(self.email_sender)

        # Password
        lbl_pwd = QLabel("Senha / App Password")
        lbl_pwd.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        sl.addWidget(lbl_pwd)
        pwd_row = QHBoxLayout()
        self.email_pwd = QLineEdit()
        self.email_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.email_pwd.setPlaceholderText("Senha de aplicativo do Gmail")
        self.email_pwd.setMinimumHeight(36)
        self.btn_show_email_pwd = QPushButton("👁")
        self.btn_show_email_pwd.setObjectName("btn-secondary")
        self.btn_show_email_pwd.setFixedSize(36, 36)
        self.btn_show_email_pwd.setCheckable(True)
        self.btn_show_email_pwd.toggled.connect(
            lambda c: self.email_pwd.setEchoMode(
                QLineEdit.EchoMode.Normal if c else QLineEdit.EchoMode.Password
            )
        )
        pwd_row.addWidget(self.email_pwd, 1)
        pwd_row.addWidget(self.btn_show_email_pwd)
        sl.addLayout(pwd_row)

        # TLS checkbox
        self.email_tls = QCheckBox("Usar STARTTLS (recomendado — porta 587)")
        self.email_tls.setStyleSheet("font-size: 13px; color: #374151;")
        self.email_tls.setChecked(True)
        sl.addWidget(self.email_tls)

        # Buttons
        btn_row = QHBoxLayout()
        btn_email_save = QPushButton("💾  Salvar Configuração")
        btn_email_save.setObjectName("btn-success")
        btn_email_save.setMinimumHeight(38)
        btn_email_save.clicked.connect(self._email_save)

        self.btn_test_email = QPushButton("🔗  Testar Conexão")
        self.btn_test_email.setObjectName("btn-secondary")
        self.btn_test_email.setMinimumHeight(38)
        self.btn_test_email.clicked.connect(self._email_test)

        self.email_test_lbl = QLabel("")
        self.email_test_lbl.setStyleSheet("font-size: 12px; color: #64748B;")

        btn_row.addWidget(btn_email_save)
        btn_row.addWidget(self.btn_test_email)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.email_test_lbl)
        btn_row.addStretch()
        sl.addLayout(btn_row)
        layout.addWidget(smtp_card)

        # ── Gmail instructions ─────────────────────────────────────────
        steps = [
            ("1", "Acesse", "myaccount.google.com/security", "https://myaccount.google.com/security", "e ative a verificação em 2 etapas."),
            ("2", "Pesquise por", "Senhas de app", None, "nas configurações de segurança do Google."),
            ("3", "Crie uma senha de app para", "\"E-mail\"", None, "— o Google gera uma senha de 16 caracteres."),
            ("4", "Use", "smtp.gmail.com", None, "porta 587 com STARTTLS e essa senha de app acima."),
            ("5", "Clique em", "Testar Conexão", None, "para confirmar que o envio funciona."),
        ]
        layout.addWidget(self._build_steps_card("Como configurar com Gmail", steps, "#EA4335"))
        layout.addStretch()
        return outer

    # ── Email actions ──────────────────────────────────────────────────────────
    def _email_save(self):
        host = self.email_host.text().strip()
        port_txt = self.email_port.text().strip()
        sender = self.email_sender.text().strip()
        pwd = self.email_pwd.text()
        if not host or not sender or not pwd:
            QMessageBox.warning(self, "Atenção", "Preencha servidor, e-mail e senha.")
            return
        try:
            port = int(port_txt) if port_txt else 587
        except ValueError:
            QMessageBox.warning(self, "Atenção", "Porta inválida.")
            return
        self.cfg.email_smtp_host = host
        self.cfg.email_smtp_port = port
        self.cfg.email_sender = sender
        self.cfg.email_password = pwd
        self.cfg.email_use_tls = self.email_tls.isChecked()
        self._email_refresh_status()
        self.email_test_lbl.setText("✓ Configuração salva!")
        QTimer.singleShot(4000, lambda: self.email_test_lbl.setText(""))

    def _email_test(self):
        host = self.email_host.text().strip()
        port_txt = self.email_port.text().strip()
        sender = self.email_sender.text().strip()
        pwd = self.email_pwd.text()
        if not host or not sender or not pwd:
            QMessageBox.warning(self, "Atenção", "Preencha os campos antes de testar.")
            return
        try:
            port = int(port_txt) if port_txt else 587
        except ValueError:
            QMessageBox.warning(self, "Atenção", "Porta inválida.")
            return
        use_tls = self.email_tls.isChecked()

        self.btn_test_email.setEnabled(False)
        self.email_test_lbl.setText("⏳ Testando conexão SMTP...")

        from PyQt6.QtCore import QThread, pyqtSignal as Signal
        from email_manager import EmailManager

        class _EmailTestWorker(QThread):
            result = Signal(bool, str)
            def __init__(self, h, p, s, pw, tls):
                super().__init__()
                self.h, self.p, self.s, self.pw, self.tls = h, p, s, pw, tls
            def run(self):
                em = EmailManager(self.h, self.p, self.s, self.pw, self.tls)
                r = em.test_connection()
                if r["success"]:
                    self.result.emit(True, "✅ Conexão SMTP bem-sucedida!")
                else:
                    self.result.emit(False, f"❌ {r.get('error', 'Erro desconhecido')[:80]}")

        self._email_test_worker = _EmailTestWorker(host, port, sender, pwd, use_tls)

        def on_result(_ok, msg):
            self.btn_test_email.setEnabled(True)
            self.email_test_lbl.setText(msg)
            QTimer.singleShot(6000, lambda: self.email_test_lbl.setText(""))

        self._email_test_worker.result.connect(on_result)
        self._email_test_worker.finished.connect(self._email_test_worker.deleteLater)
        self._email_test_worker.start()

    def _email_refresh_status(self):
        if self.cfg.email_sender and self.cfg.email_smtp_host:
            self.email_status_icon.setText("🟢")
            self.email_status_title.setText("E-mail Configurado")
            self.email_status_title.setStyleSheet("font-size:15px; font-weight:700; color:#059669;")
            self.email_status_msg.setText(
                f"Remetente: {self.cfg.email_sender}  ·  {self.cfg.email_smtp_host}:{self.cfg.email_smtp_port}"
            )
            self.email_status_card.setStyleSheet(
                "#card { background:#ECFDF5; border:1.5px solid #A7F3D0; border-radius:12px; }"
            )
        else:
            self.email_status_icon.setText("🔴")
            self.email_status_title.setText("E-mail não configurado")
            self.email_status_title.setStyleSheet("font-size:15px; font-weight:700; color:#64748B;")
            self.email_status_msg.setText(
                "Configure o servidor SMTP para enviar senhas temporárias por e-mail."
            )
            self.email_status_card.setStyleSheet(
                "#card { background:#F8FAFC; border:1.5px solid #E2E8F0; border-radius:12px; }"
            )

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _make_scroll_tab(self):
        """Return (outer_widget, content_layout) with a scroll area already wired."""
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(w)
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.addWidget(scroll)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(4, 12, 4, 12)
        layout.setSpacing(16)
        return outer, layout

    def _build_steps_card(self, title: str, steps: list, color: str) -> QFrame:
        """Build a numbered-steps instruction card with the given accent color."""
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)
        lay.addWidget(self._section_title(title))
        for num, pre, hl, url, post in steps:
            row = QHBoxLayout()
            num_lbl = QLabel(num)
            num_lbl.setFixedSize(24, 24)
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setStyleSheet(
                f"background:{color}; color:white; border-radius:12px; font-size:11px; font-weight:700;"
            )
            if url:
                txt = QLabel(f"{pre} <a href='{url}' style='color:{color}'>{hl}</a> {post}")
                txt.setOpenExternalLinks(True)
            else:
                txt = QLabel(f"{pre} <b>{hl}</b> {post}")
            txt.setStyleSheet("font-size: 13px; color: #374151;")
            txt.setWordWrap(True)
            row.addWidget(num_lbl, 0, Qt.AlignmentFlag.AlignTop)
            row.addSpacing(8)
            row.addWidget(txt, 1)
            lay.addLayout(row)
        return card

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        return lbl

    # ── Signals & state ────────────────────────────────────────────────────────
    def _connect_signals(self):
        self.fm.signals.status_changed.connect(self._on_fb_status)

    def _restore_state(self):
        # Firebase
        path = self.cfg.firebase_credentials_path
        if path:
            self.cred_path.setText(path)
        self.fb_auto_check.setChecked(self.cfg.firebase_auto_sync)
        self.fm.auto_sync = self.cfg.firebase_auto_sync
        if self.fm.is_connected:
            self._fb_apply_status("connected", "Firebase ativo.")
        else:
            self._fb_apply_status("disconnected", "Configure as credenciais para ativar.")

        # AI
        api_key = self.cfg.ai_api_key
        if api_key:
            self.ai_key_input.setText(api_key)
        idx = self.ai_model_combo.findData(self.cfg.ai_model)
        if idx >= 0:
            self.ai_model_combo.setCurrentIndex(idx)
        self._ai_refresh_status()

        # Email
        self.email_host.setText(self.cfg.email_smtp_host)
        self.email_port.setText(str(self.cfg.email_smtp_port))
        self.email_sender.setText(self.cfg.email_sender)
        if self.cfg.email_password:
            self.email_pwd.setText(self.cfg.email_password)
        self.email_tls.setChecked(self.cfg.email_use_tls)
        self._email_refresh_status()

    # ── Firebase actions ───────────────────────────────────────────────────────
    def _fb_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Service Account JSON",
            os.path.expanduser("~"), "JSON Files (*.json)",
        )
        if path:
            self.cred_path.setText(path)

    def _fb_connect(self):
        path = self.cred_path.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Atenção", "Arquivo não encontrado. Selecione um JSON válido.")
            return
        self._fb_apply_status("syncing", "Conectando ao Firebase...")
        self.fb_btn_connect.setEnabled(False)
        result = self.fm.connect(path)
        if result["success"]:
            self.cfg.firebase_credentials_path = path
            self.cfg.firebase_enabled = True
            self.fb_btn_sync.setEnabled(True)
        else:
            self.fb_btn_connect.setEnabled(True)
            QMessageBox.critical(self, "Erro ao conectar", result["error"])

    def _fb_disconnect(self):
        reply = QMessageBox.question(
            self, "Desconectar",
            "Desconectar do Firebase?\nOs dados locais não serão afetados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.fm.disconnect()
            self.cfg.firebase_enabled = False
            self.fb_btn_sync.setEnabled(False)

    def _fb_sync_all(self):
        if not self.fm.is_connected:
            return
        self.fb_btn_sync.setEnabled(False)
        self.fb_sync_lbl.setText("⏳ Sincronizando...")
        self.fm.sync_all(self.db, self.user_id)
        QTimer.singleShot(5000, lambda: (
            self.fb_btn_sync.setEnabled(True),
            self.fb_sync_lbl.setText(""),
        ))

    def _fb_auto_toggled(self, checked: bool):
        self.fm.auto_sync = checked
        self.cfg.firebase_auto_sync = checked

    def _on_fb_status(self, status: str, message: str):
        self._fb_apply_status(status, message)
        if status == "synced":
            self.fb_sync_lbl.setText(f"✓ {message}")
            QTimer.singleShot(3000, lambda: self.fb_sync_lbl.setText(""))

    def _fb_apply_status(self, status: str, message: str):
        meta = STATUS_STYLES.get(status, STATUS_STYLES["disconnected"])
        icon, title, bg, fg, border = meta
        self.fb_icon.setText(icon)
        self.fb_title.setText(title)
        self.fb_msg.setText(message)
        self.fb_status_card.setStyleSheet(
            f"#card {{ background:{bg}; border:1.5px solid {border}; border-radius:12px; }}"
        )
        self.fb_title.setStyleSheet(f"font-size:15px; font-weight:700; color:{fg};")
        connected = self.fm.is_connected
        self.fb_btn_connect.setVisible(not connected)
        self.fb_btn_connect.setEnabled(True)
        self.fb_btn_disconnect.setVisible(connected)
        self.fb_btn_sync.setEnabled(connected)
        if self.fm.last_sync:
            ts = self.fm.last_sync.strftime("%d/%m/%Y às %H:%M:%S")
            self.fb_sync_time.setText(f"Última sincronização: {ts}")

    # ── AI actions ─────────────────────────────────────────────────────────────
    def _ai_save(self):
        key = self.ai_key_input.text().strip()
        model = self.ai_model_combo.currentData()
        if not key:
            QMessageBox.warning(self, "Atenção", "Insira a chave de API antes de salvar.")
            return
        if not key.startswith("sk-ant-"):
            QMessageBox.warning(self, "Atenção", "Chave inválida — deve começar com 'sk-ant-'.")
            return
        self.cfg.ai_api_key = key
        self.cfg.ai_model = model
        self._ai_refresh_status()
        self.ai_test_lbl.setText("✓ Salvo! Acesse 🤖 IA Insights para começar.")
        QTimer.singleShot(4000, lambda: self.ai_test_lbl.setText(""))

    def _ai_test(self):
        key = self.ai_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Atenção", "Insira a chave antes de testar.")
            return
        self.btn_test_ai.setEnabled(False)
        self.ai_test_lbl.setText("⏳ Testando conexão...")

        from PyQt6.QtCore import QThread, pyqtSignal as Signal

        class _TestWorker(QThread):
            result = Signal(bool, str)
            def __init__(self, k, m):
                super().__init__()
                self.k = k
                self.m = m
            def run(self):
                try:
                    import anthropic  # type: ignore[import-untyped]
                    client = anthropic.Anthropic(api_key=self.k)
                    client.messages.create(
                        model=self.m,
                        max_tokens=5,
                        messages=[{"role": "user", "content": "ok"}],
                    )
                    self.result.emit(True, "✅ Conexão bem-sucedida!")
                except ImportError:
                    self.result.emit(False, "❌ pip install anthropic")
                except Exception as e:
                    self.result.emit(False, f"❌ {str(e)[:80]}")

        self._test_worker = _TestWorker(key, self.ai_model_combo.currentData())

        def on_result(ok, msg):
            self.btn_test_ai.setEnabled(True)
            self.ai_test_lbl.setText(msg)
            if ok:
                self._ai_refresh_status()
            QTimer.singleShot(5000, lambda: self.ai_test_lbl.setText(""))

        self._test_worker.result.connect(on_result)
        self._test_worker.finished.connect(self._test_worker.deleteLater)
        self._test_worker.start()

    def _ai_refresh_status(self):
        key = self.cfg.ai_api_key
        model = self.cfg.ai_model
        if key and key.startswith("sk-ant-"):
            model_name = model.split("-")[1].capitalize() if "-" in model else model
            self.ai_status_icon.setText("🟢")
            self.ai_status_title.setText("IA Configurada")
            self.ai_status_title.setStyleSheet("font-size:15px; font-weight:700; color:#059669;")
            self.ai_status_msg.setText(f"Modelo: {model_name} — acesse 🤖 IA Insights para gerar análises.")
            self.ai_status_card.setStyleSheet(
                "#card { background:#ECFDF5; border:1.5px solid #A7F3D0; border-radius:12px; }"
            )
        else:
            self.ai_status_icon.setText("🔴")
            self.ai_status_title.setText("IA não configurada")
            self.ai_status_title.setStyleSheet("font-size:15px; font-weight:700; color:#64748B;")
            self.ai_status_msg.setText("Insira sua chave da API Anthropic e salve para ativar.")
            self.ai_status_card.setStyleSheet(
                "#card { background:#F8FAFC; border:1.5px solid #E2E8F0; border-radius:12px; }"
            )

    def refresh(self):
        self._restore_state()
