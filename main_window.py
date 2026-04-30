from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt
from styles import MAIN_STYLE
from animated_logo import AnimatedLogo
from dashboard_widget import DashboardWidget
from transactions_widget import TransactionsWidget
from accounts_widget import AccountsWidget
from categories_widget import CategoriesWidget
from reports_widget import ReportsWidget
from budgets_widget import BudgetsWidget
from settings_widget import SettingsWidget
from ai_widget import AIWidget
from admin_widget import AdminWidget
from firebase_manager import FirebaseManager
from config_manager import ConfigManager


NAV_ITEMS = [
    ("dashboard",    "🏠", "Dashboard"),
    ("transactions", "💳", "Transações"),
    ("accounts",     "🏦", "Contas"),
    ("categories",   "🏷️", "Categorias"),
    ("budgets",      "🎯", "Orçamentos"),
    ("reports",      "📊", "Relatórios"),
    ("ai",           "🤖", "IA Insights"),
    ("settings",     "⚙️", "Configurações"),
]

PAGE_META = {
    "dashboard":    ("Dashboard",       "Visão geral das suas finanças"),
    "transactions": ("Transações",      "Registre e gerencie suas movimentações"),
    "accounts":     ("Contas",          "Gerencie suas contas bancárias"),
    "categories":   ("Categorias",      "Organize categorias de receita e despesa"),
    "budgets":      ("Orçamentos",      "Defina e acompanhe limites mensais"),
    "reports":      ("Relatórios",      "Análises e gráficos detalhados"),
    "ai":           ("IA Insights",     "Análises inteligentes e previsões com Claude AI"),
    "settings":     ("Configurações",   "Preferências, Firebase e Inteligência Artificial"),
    "admin":        ("Administração",   "Gerenciar usuários e permissões do sistema"),
}

# Status badge styles per Firebase state
_BADGE = {
    "connected":    ("🟢", "#ECFDF5", "#059669"),
    "disconnected": ("⚫", "#F1F5F9", "#94A3B8"),
    "syncing":      ("🔄", "#EFF6FF", "#2563EB"),
    "synced":       ("🟢", "#ECFDF5", "#059669"),
    "error":        ("🔴", "#FEF2F2", "#DC2626"),
}


class MainWindow(QMainWindow):
    def __init__(self, db, user: dict):
        super().__init__()
        self.db = db
        self.user = user
        self.nav_buttons: dict[str, QPushButton] = {}

        # ── Firebase & Config ──────────────────────────────────────────────
        self.cfg = ConfigManager()
        self.fm = FirebaseManager()
        self.fm.auto_sync = self.cfg.firebase_auto_sync
        self.db.set_firebase_manager(self.fm)
        self.fm.signals.status_changed.connect(self._on_firebase_status)

        # Auto-reconnect if credentials were saved
        if self.cfg.firebase_enabled and self.cfg.firebase_credentials_path:
            import os
            if os.path.exists(self.cfg.firebase_credentials_path):
                self.fm.connect(self.cfg.firebase_credentials_path)

        self.setWindowTitle("URANNIO")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)
        self.setStyleSheet(MAIN_STYLE)

        self._build_ui()
        self._navigate("dashboard")
        self._center_window()

    def _center_window(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())
        layout.addLayout(self._build_content_area(), 1)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_w = QWidget()
        logo_w.setObjectName("sidebar")
        logo_lay = QHBoxLayout(logo_w)
        logo_lay.setContentsMargins(8, 12, 8, 8)
        logo_lay.setSpacing(4)
        logo_icon = AnimatedLogo(size=28)
        logo_txt = QLabel("URANNIO")
        logo_txt.setObjectName("logo-label")
        logo_lay.addWidget(logo_icon)
        logo_lay.addWidget(logo_txt)
        logo_lay.addStretch()
        layout.addWidget(logo_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
        layout.addWidget(sep)
        layout.addSpacing(8)

        sec_lbl = QLabel("MENU PRINCIPAL")
        sec_lbl.setObjectName("section-label")
        layout.addWidget(sec_lbl)

        for key, icon, label in NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)

        if self.user.get("role") == "admin":
            sep2 = QFrame()
            sep2.setFrameShape(QFrame.Shape.HLine)
            sep2.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
            layout.addWidget(sep2)
            layout.addSpacing(4)
            adm_lbl = QLabel("ADMINISTRAÇÃO")
            adm_lbl.setObjectName("section-label")
            layout.addWidget(adm_lbl)
            btn_admin = QPushButton("  👑  Usuários")
            btn_admin.setObjectName("nav-btn")
            btn_admin.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_admin.clicked.connect(lambda: self._navigate("admin"))
            self.nav_buttons["admin"] = btn_admin
            layout.addWidget(btn_admin)

        layout.addStretch()

        # User panel
        user_panel = QWidget()
        user_panel.setObjectName("user-panel")
        up_lay = QVBoxLayout(user_panel)
        up_lay.setContentsMargins(0, 0, 0, 0)
        up_lay.setSpacing(4)

        row = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 22px;")

        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(self.user.get("username", "Usuário"))
        name_lbl.setObjectName("user-name")
        email_lbl = QLabel(self.user.get("email", ""))
        email_lbl.setObjectName("user-email")
        email_lbl.setMaximumWidth(130)
        info.addWidget(name_lbl)
        info.addWidget(email_lbl)

        btn_logout = QPushButton("⏻")
        btn_logout.setObjectName("logout-btn")
        btn_logout.setToolTip("Sair")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.clicked.connect(self._logout)

        row.addWidget(avatar)
        row.addSpacing(6)
        row.addLayout(info)
        row.addStretch()
        row.addWidget(btn_logout)
        up_lay.addLayout(row)

        layout.addWidget(user_panel)
        layout.addSpacing(8)

        return sidebar

    # ── Content area ───────────────────────────────────────────────────────────
    def _build_content_area(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setObjectName("topbar")
        tb_lay = QHBoxLayout(topbar)
        tb_lay.setContentsMargins(24, 0, 20, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("page-title")
        self.page_subtitle = QLabel("Visão geral das suas finanças")
        self.page_subtitle.setObjectName("page-subtitle")
        title_col.addWidget(self.page_title)
        title_col.addWidget(self.page_subtitle)

        tb_lay.addLayout(title_col)
        tb_lay.addStretch()

        # ── Firebase status badge ──────────────────────────────────────────
        self.fb_badge = QFrame()
        self.fb_badge.setObjectName("card")
        self.fb_badge.setFixedHeight(36)
        badge_lay = QHBoxLayout(self.fb_badge)
        badge_lay.setContentsMargins(10, 0, 14, 0)
        badge_lay.setSpacing(6)

        self.fb_badge_icon = QLabel("⚫")
        self.fb_badge_icon.setStyleSheet("font-size: 11px;")
        self.fb_badge_text = QLabel("Firebase: Offline")
        self.fb_badge_text.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8;")

        badge_lay.addWidget(self.fb_badge_icon)
        badge_lay.addWidget(self.fb_badge_text)

        self.fb_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fb_badge.mousePressEvent = lambda e: self._navigate("settings")

        tb_lay.addWidget(self.fb_badge)

        layout.addWidget(topbar)

        # Stacked pages
        self.stack = QStackedWidget()
        user_id = self.user["id"]

        self.pages = {
            "dashboard":    DashboardWidget(self.db, user_id),
            "transactions": TransactionsWidget(self.db, user_id),
            "accounts":     AccountsWidget(self.db, user_id),
            "categories":   CategoriesWidget(self.db, user_id),
            "budgets":      BudgetsWidget(self.db, user_id),
            "reports":      ReportsWidget(self.db, user_id),
            "ai":           AIWidget(self.db, user_id, self.cfg),
            "settings":     SettingsWidget(self.db, user_id, self.fm, self.cfg),
        }
        if self.user.get("role") == "admin":
            self.pages["admin"] = AdminWidget(self.db, user_id, self.cfg)

        for page in self.pages.values():
            self.stack.addWidget(page)

        layout.addWidget(self.stack, 1)
        return layout

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _navigate(self, key: str):
        for k, btn in self.nav_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        title, subtitle = PAGE_META.get(key, (key, ""))
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        if hasattr(page, "refresh"):
            page.refresh()

    # ── Firebase badge ──────────────────────────────────────────────────────────
    def _on_firebase_status(self, status: str, _message: str):
        icon, bg, fg = _BADGE.get(status, _BADGE["disconnected"])

        labels = {
            "connected":    "Firebase: Ativo",
            "disconnected": "Firebase: Offline",
            "syncing":      "Sincronizando...",
            "synced":       "Firebase: Sincronizado",
            "error":        "Firebase: Erro",
        }
        self.fb_badge_icon.setText(icon)
        self.fb_badge_text.setText(labels.get(status, status))
        self.fb_badge_text.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {fg};")
        self.fb_badge.setStyleSheet(
            f"#card {{ background: {bg}; border: 1px solid {fg}33; border-radius: 8px; }}"
        )

    # ── Logout ─────────────────────────────────────────────────────────────────
    def _logout(self):
        reply = QMessageBox.question(
            self, "Sair",
            "Deseja realmente sair do sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from login_window import LoginWindow
            from PyQt6.QtWidgets import QApplication
            self.login_win = LoginWindow(self.db)

            def on_login(user):
                self.login_win.close()
                new_win = MainWindow(self.db, user)
                new_win.show()
                QApplication.instance().new_win = new_win

            self.login_win.login_successful.connect(on_login)
            self.login_win.show()
            self.close()
