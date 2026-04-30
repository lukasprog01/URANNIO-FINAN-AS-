MAIN_STYLE = """
    QMainWindow, QWidget {
        background-color: #F0F4F8;
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    QDialog {
        background-color: #F0F4F8;
    }

    /* ── Sidebar ─────────────────────────────────────────────────────────── */
    #sidebar {
        background-color: #0F172A;
        border: none;
        min-width: 220px;
        max-width: 220px;
    }

    #logo-label {
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 800;
        padding: 0px;
        letter-spacing: 4px;
    }

    #nav-btn {
        background: transparent;
        color: #94A3B8;
        border: none;
        border-radius: 8px;
        padding: 11px 16px;
        text-align: left;
        font-size: 13px;
        font-weight: 500;
        margin: 2px 8px;
    }

    #nav-btn:hover {
        background-color: #1E293B;
        color: #E2E8F0;
    }

    #nav-btn[active="true"] {
        background-color: #3B82F6;
        color: #FFFFFF;
        font-weight: 600;
    }

    #section-label {
        color: #475569;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 8px 24px 4px 24px;
    }

    #user-panel {
        background-color: #1E293B;
        border-radius: 10px;
        margin: 8px;
        padding: 12px;
    }

    #user-name {
        color: #E2E8F0;
        font-size: 13px;
        font-weight: 600;
    }

    #user-email {
        color: #64748B;
        font-size: 11px;
    }

    #logout-btn {
        background: transparent;
        color: #64748B;
        border: none;
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
    }

    #logout-btn:hover {
        background-color: #334155;
        color: #EF4444;
    }

    /* ── Top bar ─────────────────────────────────────────────────────────── */
    #topbar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        min-height: 56px;
        max-height: 56px;
    }

    #page-title {
        color: #0F172A;
        font-size: 18px;
        font-weight: 700;
    }

    #page-subtitle {
        color: #64748B;
        font-size: 12px;
    }

    /* ── Cards ───────────────────────────────────────────────────────────── */
    #card {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }

    #stat-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }

    #stat-value {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
    }

    #stat-label {
        font-size: 12px;
        color: #64748B;
        font-weight: 500;
    }

    #stat-icon {
        font-size: 28px;
    }

    /* ── Buttons ─────────────────────────────────────────────────────────── */
    QPushButton {
        background-color: #3B82F6;
        color: white;
        border: none;
        border-radius: 7px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        min-height: 34px;
    }

    QPushButton:hover {
        background-color: #2563EB;
    }

    QPushButton:pressed {
        background-color: #1D4ED8;
    }

    QPushButton:disabled {
        background-color: #CBD5E1;
        color: #94A3B8;
    }

    QPushButton#btn-danger {
        background-color: #EF4444;
    }

    QPushButton#btn-danger:hover {
        background-color: #DC2626;
    }

    QPushButton#btn-secondary {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #E2E8F0;
    }

    QPushButton#btn-secondary:hover {
        background-color: #E2E8F0;
        color: #334155;
    }

    QPushButton#btn-success {
        background-color: #10B981;
    }

    QPushButton#btn-success:hover {
        background-color: #059669;
    }

    QPushButton#btn-warning {
        background-color: #F59E0B;
    }

    QPushButton#btn-warning:hover {
        background-color: #D97706;
    }

    QPushButton#btn-icon {
        background: transparent;
        color: #64748B;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 6px;
        min-width: 34px;
        min-height: 34px;
        font-size: 15px;
    }

    QPushButton#btn-icon:hover {
        background-color: #F1F5F9;
        color: #1E293B;
    }

    /* ── Inputs ──────────────────────────────────────────────────────────── */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 7px;
        padding: 8px 12px;
        font-size: 13px;
        color: #1E293B;
        selection-background-color: #BFDBFE;
    }

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1.5px solid #3B82F6;
        background-color: #FAFCFF;
    }

    QDateEdit, QDoubleSpinBox, QSpinBox {
        background-color: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 7px;
        padding: 7px 10px;
        font-size: 13px;
        color: #1E293B;
    }

    QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
        border: 1.5px solid #3B82F6;
    }

    QDateEdit::drop-down, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
    QSpinBox::up-button, QSpinBox::down-button {
        border: none;
        background: transparent;
    }

    QComboBox {
        background-color: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 7px;
        padding: 7px 12px;
        font-size: 13px;
        color: #1E293B;
        min-height: 34px;
    }

    QComboBox:focus {
        border: 1.5px solid #3B82F6;
    }

    QComboBox::drop-down {
        border: none;
        padding-right: 8px;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        selection-background-color: #EFF6FF;
        selection-color: #1E40AF;
        padding: 4px;
    }

    /* ── Tables ──────────────────────────────────────────────────────────── */
    QTableWidget {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        gridline-color: #F8FAFC;
        font-size: 13px;
        alternate-background-color: #FAFAFA;
    }

    QTableWidget::item {
        padding: 10px 12px;
        border: none;
        color: #334155;
    }

    QTableWidget::item:selected {
        background-color: #EFF6FF;
        color: #1E40AF;
    }

    QHeaderView::section {
        background-color: #F8FAFC;
        color: #64748B;
        font-weight: 600;
        font-size: 12px;
        padding: 10px 12px;
        border: none;
        border-bottom: 2px solid #E2E8F0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    QTableWidget::item:alternate {
        background-color: #FAFAFA;
    }

    /* ── Scrollbars ───────────────────────────────────────────────────────── */
    QScrollBar:vertical {
        width: 7px;
        background: transparent;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background: #CBD5E1;
        border-radius: 3px;
        min-height: 24px;
    }

    QScrollBar::handle:vertical:hover {
        background: #94A3B8;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }

    QScrollBar:horizontal {
        height: 7px;
        background: transparent;
    }

    QScrollBar::handle:horizontal {
        background: #CBD5E1;
        border-radius: 3px;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }

    /* ── Labels ──────────────────────────────────────────────────────────── */
    QLabel {
        color: #334155;
        background: transparent;
    }

    #title-label {
        color: #0F172A;
        font-size: 15px;
        font-weight: 700;
    }

    #subtitle-label {
        color: #64748B;
        font-size: 12px;
    }

    #amount-positive {
        color: #059669;
        font-weight: 700;
    }

    #amount-negative {
        color: #DC2626;
        font-weight: 700;
    }

    /* ── Tab Widget ───────────────────────────────────────────────────────── */
    QTabWidget::pane {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        background-color: #FFFFFF;
        top: -1px;
    }

    QTabBar::tab {
        padding: 9px 22px;
        font-size: 13px;
        color: #64748B;
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        font-weight: 500;
    }

    QTabBar::tab:selected {
        color: #3B82F6;
        border-bottom: 2px solid #3B82F6;
        font-weight: 600;
    }

    QTabBar::tab:hover:!selected {
        color: #334155;
    }

    /* ── Message Box ─────────────────────────────────────────────────────── */
    QMessageBox {
        background-color: #FFFFFF;
    }

    QMessageBox QPushButton {
        min-width: 80px;
    }

    /* ── Group Box ───────────────────────────────────────────────────────── */
    QGroupBox {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        margin-top: 12px;
        font-size: 13px;
        font-weight: 600;
        color: #334155;
        background-color: #FFFFFF;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #475569;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
"""

LOGIN_STYLE = """
    QMainWindow, QWidget#login-root {
        background-color: #0F172A;
    }

    QWidget#login-card {
        background-color: #FFFFFF;
        border-radius: 20px;
    }

    QLabel#app-name {
        color: #FFFFFF;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: 10px;
    }

    QLabel#app-tagline {
        color: #64748B;
        font-size: 14px;
    }

    QLabel#form-title {
        color: #0F172A;
        font-size: 22px;
        font-weight: 700;
    }

    QLabel#form-subtitle {
        color: #64748B;
        font-size: 13px;
    }

    QLabel#field-label {
        color: #374151;
        font-size: 13px;
        font-weight: 600;
    }

    QLabel#error-label {
        color: #EF4444;
        font-size: 12px;
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 6px;
        padding: 6px 12px;
    }

    QLabel#success-label {
        color: #059669;
        font-size: 12px;
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-radius: 6px;
        padding: 6px 12px;
    }

    QLineEdit {
        background-color: #F8FAFC;
        border: 1.5px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
        color: #1E293B;
        min-height: 38px;
    }

    QLineEdit:focus {
        border: 1.5px solid #3B82F6;
        background-color: #FAFCFF;
    }

    QPushButton#btn-login {
        background-color: #3B82F6;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        min-height: 44px;
        padding: 0 20px;
    }

    QPushButton#btn-login:hover {
        background-color: #2563EB;
    }

    QPushButton#btn-login:pressed {
        background-color: #1D4ED8;
    }

    QPushButton#btn-link {
        background: transparent;
        color: #3B82F6;
        border: none;
        font-size: 13px;
        font-weight: 500;
        padding: 0;
        text-decoration: underline;
    }

    QPushButton#btn-link:hover {
        color: #1D4ED8;
    }

    QCheckBox {
        color: #64748B;
        font-size: 13px;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1.5px solid #CBD5E1;
        border-radius: 4px;
        background: white;
    }

    QCheckBox::indicator:checked {
        background-color: #3B82F6;
        border-color: #3B82F6;
    }
"""
