from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QScrollArea, QApplication, QLineEdit,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from ai_manager import (
    AIWorker, ANALYSIS_PROMPTS, SYSTEM_PROMPT, prepare_financial_context
)


ANALYSIS_CARDS = [
    ("spending",  "📊", "Análise de\nGastos",          "#EFF6FF", "#3B82F6"),
    ("prediction","📈", "Previsão\nFinanceira",         "#ECFDF5", "#059669"),
    ("savings",   "💡", "Oportunidades\nde Economia",   "#FFFBEB", "#D97706"),
    ("health",    "🎯", "Saúde\nFinanceira",            "#F5F3FF", "#7C3AED"),
    ("longterm",  "🔮", "Projeção de\nLongo Prazo",     "#FFF1F2", "#E11D48"),
]

class AnalysisCard(QPushButton):
    def __init__(self, key, icon, label, bg, accent, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedSize(148, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")

        text_lbl = QLabel(label)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {accent}; "
            "background: transparent; line-height: 1.3;"
        )

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)

        self._bg = bg
        self._accent = accent
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet(
                f"QPushButton {{ background: {self._accent}; border: 2px solid {self._accent}; "
                f"border-radius: 10px; }} "
                f"QLabel {{ color: white; }}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{ background: {self._bg}; border: 2px solid {self._accent}33; "
                f"border-radius: 10px; }} "
                f"QPushButton:hover {{ background: {self._accent}22; "
                f"border: 2px solid {self._accent}66; }}"
            )

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)


class AIWidget(QWidget):
    def __init__(self, db, user_id: int, cfg):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.cfg = cfg
        self._worker: AIWorker | None = None
        self._selected_type = "spending"
        self._cards: dict[str, AnalysisCard] = {}
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
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Header: data context summary ──────────────────────────────────
        layout.addWidget(self._build_context_summary())

        # ── Analysis type buttons ──────────────────────────────────────────
        types_card = QFrame()
        types_card.setObjectName("card")
        types_lay = QVBoxLayout(types_card)
        types_lay.setContentsMargins(20, 16, 20, 16)
        types_lay.setSpacing(10)

        lbl_type = QLabel("Escolha o tipo de análise:")
        lbl_type.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        types_lay.addWidget(lbl_type)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        for key, icon, label, bg, accent in ANALYSIS_CARDS:
            card = AnalysisCard(key, icon, label, bg, accent)
            card.clicked.connect(lambda checked, k=key: self._select_type(k))
            self._cards[key] = card
            cards_row.addWidget(card)
        cards_row.addStretch()
        types_lay.addLayout(cards_row)
        layout.addWidget(types_card)

        # ── Custom question ────────────────────────────────────────────────
        custom_card = QFrame()
        custom_card.setObjectName("card")
        custom_lay = QVBoxLayout(custom_card)
        custom_lay.setContentsMargins(20, 14, 20, 14)
        custom_lay.setSpacing(8)

        lbl_custom = QLabel("💬  Ou faça uma pergunta personalizada:")
        lbl_custom.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        custom_lay.addWidget(lbl_custom)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText(
            "Ex: Por que meus gastos com alimentação subiram? Quando vou quitar minhas dívidas?..."
        )
        self.custom_input.setMinimumHeight(36)
        self.custom_input.returnPressed.connect(self._run_custom)

        btn_custom = QPushButton("Perguntar")
        btn_custom.setMinimumHeight(36)
        btn_custom.setMinimumWidth(110)
        btn_custom.clicked.connect(self._run_custom)

        input_row.addWidget(self.custom_input, 1)
        input_row.addWidget(btn_custom)
        custom_lay.addLayout(input_row)
        layout.addWidget(custom_card)

        # Select first card by default (must be after custom_input is created)
        self._select_type("spending")

        # ── Generate button ────────────────────────────────────────────────
        gen_row = QHBoxLayout()
        self.btn_generate = QPushButton("✨  Gerar Análise com IA")
        self.btn_generate.setObjectName("btn-success")
        self.btn_generate.setMinimumHeight(44)
        self.btn_generate.setMinimumWidth(220)
        self.btn_generate.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: 600; } "
            "QPushButton#btn-success { background: #7C3AED; } "
            "QPushButton#btn-success:hover { background: #6D28D9; }"
        )
        self.btn_generate.clicked.connect(self._run_analysis)

        self.btn_stop = QPushButton("⏹  Parar")
        self.btn_stop.setObjectName("btn-danger")
        self.btn_stop.setMinimumHeight(44)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self._stop_analysis)

        self.lbl_model = QLabel("")
        self.lbl_model.setStyleSheet("font-size: 12px; color: #94A3B8;")

        gen_row.addWidget(self.btn_generate)
        gen_row.addWidget(self.btn_stop)
        gen_row.addSpacing(12)
        gen_row.addWidget(self.lbl_model, 1)
        layout.addLayout(gen_row)

        # ── Response display ───────────────────────────────────────────────
        layout.addWidget(self._build_response_area(), 1)

    def _build_context_summary(self):
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "#card { background: linear-gradient(135deg, #1E293B, #0F172A); "
            "border-radius: 12px; border: none; }"
        )
        lay = QHBoxLayout(card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("🤖  Assistente Financeiro com IA")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC;")
        sub = QLabel("Análise inteligente dos seus dados financeiros com Claude AI")
        sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        left.addWidget(title)
        left.addWidget(sub)

        right = QHBoxLayout()
        right.setSpacing(16)

        self.stat_transactions = self._mini_stat("💳", "0", "transações")
        self.stat_months = self._mini_stat("📅", "0", "meses de dados")
        self.stat_accounts = self._mini_stat("🏦", "0", "contas")

        right.addWidget(self.stat_transactions)
        right.addWidget(self.stat_accounts)
        right.addWidget(self.stat_months)

        lay.addLayout(left, 1)
        lay.addLayout(right)
        return card

    def _mini_stat(self, icon: str, value: str, label: str):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout()
        row.setSpacing(4)
        ico = QLabel(icon)
        ico.setStyleSheet("font-size: 16px;")
        val = QLabel(value)
        val.setStyleSheet("font-size: 18px; font-weight: 700; color: #F8FAFC;")
        row.addWidget(ico)
        row.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; color: #64748B;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addLayout(row)
        lay.addWidget(lbl)

        # store ref for update
        val.setObjectName(f"stat_val_{label.replace(' ', '_')}")
        w._val_lbl = val
        return w

    def _build_response_area(self):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(380)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🤖  Análise da IA")
        title.setObjectName("title-label")

        self.lbl_tokens = QLabel("")
        self.lbl_tokens.setStyleSheet("font-size: 11px; color: #94A3B8;")

        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setObjectName("btn-secondary")
        btn_copy.setFixedHeight(28)
        btn_copy.clicked.connect(self._copy_response)

        btn_clear = QPushButton("🗑️ Limpar")
        btn_clear.setObjectName("btn-secondary")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._clear_response)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self.lbl_tokens)
        hdr.addSpacing(8)
        hdr.addWidget(btn_copy)
        hdr.addWidget(btn_clear)
        lay.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #F1F5F9; max-height: 1px; border: none;")
        lay.addWidget(sep)

        # Placeholder label (shown when empty)
        self.placeholder = QLabel(
            "Selecione um tipo de análise acima e clique em\n"
            "✨ Gerar Análise com IA para começar.\n\n"
            "Certifique-se de configurar sua chave de API\nna tela de Configurações → IA."
        )
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #CBD5E1; font-size: 14px; padding: 40px;")
        lay.addWidget(self.placeholder)

        # Actual text display
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setVisible(False)
        self.response_display.setStyleSheet(
            "QTextEdit { background: #FAFCFF; border: none; font-size: 13.5px; "
            "color: #1E293B; line-height: 1.6; padding: 4px; }"
        )
        font = QFont("Segoe UI", 10)
        self.response_display.setFont(font)
        lay.addWidget(self.response_display, 1)

        # Progress bar (streaming indicator)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # indeterminate
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: #F1F5F9; border-radius: 1px; } "
            "QProgressBar::chunk { background: #7C3AED; border-radius: 1px; }"
        )
        lay.addWidget(self.progress_bar)

        return card

    # ── Data refresh ───────────────────────────────────────────────────────────
    def refresh(self):
        self.stat_transactions._val_lbl.setText(str(self.db.get_transaction_count(self.user_id)))
        self.stat_accounts._val_lbl.setText(str(len(self.db.get_accounts(self.user_id))))
        self.stat_months._val_lbl.setText(str(self.db.get_transaction_months(self.user_id)))

        # Update model label
        model = self.cfg.ai_model
        model_label = model.split("-")[1].capitalize() if "-" in model else model
        self.lbl_model.setText(f"Modelo: {model_label}")

    # ── Type selection ─────────────────────────────────────────────────────────
    def _select_type(self, key: str):
        self._selected_type = key
        for k, card in self._cards.items():
            card.setChecked(k == key)
        self.custom_input.clear()

    # ── Analysis execution ─────────────────────────────────────────────────────
    def _run_analysis(self):
        key = self._selected_type
        _, question = ANALYSIS_PROMPTS[key]
        self._start_worker(question)

    def _run_custom(self):
        question = self.custom_input.text().strip()
        if not question:
            return
        for card in self._cards.values():
            card.setChecked(False)
        self._selected_type = ""
        self._start_worker(question)

    def _start_worker(self, question: str):
        api_key = self.cfg.ai_api_key
        if not api_key:
            self._show_error(
                "⚠️  Chave de API não configurada.\n\n"
                "Vá em Configurações → Inteligência Artificial\n"
                "e insira sua chave da API Anthropic."
            )
            return

        if self._worker and self._worker.isRunning():
            return

        context = prepare_financial_context(self.db, self.user_id)
        prompt = f"{context}\n\n{'='*55}\nPERGUNTA DO USUÁRIO:\n{question}"

        if self._worker:
            self._worker.chunk.disconnect()
            self._worker.done.disconnect()
            self._worker.error.disconnect()
            self._worker.deleteLater()

        model = self.cfg.ai_model
        self._worker = AIWorker(api_key, model, SYSTEM_PROMPT, prompt)
        self._worker.chunk.connect(self._on_chunk)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)

        self._full_response = ""
        self.response_display.clear()
        self.response_display.setVisible(True)
        self.placeholder.setVisible(False)
        self.progress_bar.setVisible(True)
        self.btn_generate.setEnabled(False)
        self.btn_stop.setVisible(True)
        self.lbl_tokens.setText("Gerando análise...")

        # Show analysis type header
        if self._selected_type in ANALYSIS_PROMPTS:
            header_title, _ = ANALYSIS_PROMPTS[self._selected_type]
            self.response_display.setPlainText(f"{header_title}\n{'─'*40}\n\n")
            self.response_display.moveCursor(QTextCursor.MoveOperation.End)

        self._worker.start()

    def _stop_analysis(self):
        if self._worker:
            self._worker.cancel()
            self._worker.quit()
        self._reset_controls()
        self.lbl_tokens.setText("Geração interrompida.")

    def _on_chunk(self, text: str):
        cursor = self.response_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.response_display.setTextCursor(cursor)
        self.response_display.ensureCursorVisible()

    def _on_done(self, tokens: int):
        self._reset_controls()
        self.lbl_tokens.setText(f"✓ Concluído · {tokens:,} tokens usados")

    def _on_error(self, msg: str):
        self._reset_controls()
        self._show_error(msg)

    def _reset_controls(self):
        self.progress_bar.setVisible(False)
        self.btn_generate.setEnabled(True)
        self.btn_stop.setVisible(False)

    def _show_error(self, msg: str):
        self.response_display.setPlainText(f"❌  ERRO\n\n{msg}")
        self.response_display.setVisible(True)
        self.placeholder.setVisible(False)

    def _copy_response(self):
        text = self.response_display.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.lbl_tokens.setText("✓ Copiado para a área de transferência!")
            QTimer.singleShot(2500, lambda: self.lbl_tokens.setText(""))

    def _clear_response(self):
        self.response_display.clear()
        self.response_display.setVisible(False)
        self.placeholder.setVisible(True)
        self.lbl_tokens.setText("")
