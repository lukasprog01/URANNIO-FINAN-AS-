"""URANNIO Finanças — Instalador Interativo v1.0"""

import sys
import os
import shutil
import subprocess
import ctypes
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFrame, QStackedWidget,
    QProgressBar, QFileDialog, QCheckBox, QMessageBox,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import QPainter, QColor, QLinearGradient

try:
    from animated_logo import AnimatedLogo
    HAS_LOGO = True
except ImportError:
    HAS_LOGO = False

APP_NAME  = "URANNIO Finanças"
APP_VER   = "1.0"
PUBLISHER = "Lukas"
APP_EXE   = "URANNIO.exe"
REG_KEY   = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\URANNIOFinancas"
DEFAULT_DIR = str(Path("C:/Program Files") / APP_NAME)


def resource(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1,
    )
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 340)
        self._build()
        self._center()

        self._dots = ["", ".", "..", "..."]
        self._dot_idx = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._tick_dots)
        self._dot_timer.start(400)

        QTimer.singleShot(3200, self.finished)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        bg = QFrame()
        bg.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #0F172A, stop:1 #064E3B); border-radius: 20px; }"
        )
        bl = QVBoxLayout(bg)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.setSpacing(10)
        bl.setContentsMargins(32, 32, 32, 28)

        if HAS_LOGO:
            logo = AnimatedLogo(size=72)
            bl.addWidget(logo, 0, Qt.AlignmentFlag.AlignCenter)

        title = QLabel("URANNIO")
        title.setStyleSheet(
            "font-size: 38px; font-weight: 800; color: #FFFFFF; letter-spacing: 10px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Controle Financeiro")
        sub.setStyleSheet("font-size: 14px; color: #6EE7B7; letter-spacing: 3px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ver = QLabel(f"Versão {APP_VER}")
        ver.setStyleSheet("font-size: 11px; color: #334155; margin-top: 4px;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._loading_lbl = QLabel("Iniciando instalador")
        self._loading_lbl.setStyleSheet("font-size: 12px; color: #475569; margin-top: 16px;")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for w in [title, sub, ver, self._loading_lbl]:
            bl.addWidget(w)

        lay.addWidget(bg)

    def _tick_dots(self):
        self._dot_idx = (self._dot_idx + 1) % len(self._dots)
        self._loading_lbl.setText(f"Iniciando instalador{self._dots[self._dot_idx]}")

    def _center(self):
        g = QApplication.primaryScreen().geometry()
        self.move((g.width() - self.width()) // 2, (g.height() - self.height()) // 2)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(96)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(32, 0, 32, 0)
        lay.setSpacing(14)

        if HAS_LOGO:
            lay.addWidget(AnimatedLogo(size=32))

        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: 2px;"
        )
        self._page_lbl = QLabel("Bem-vindo")
        self._page_lbl.setStyleSheet("font-size: 12px; color: #6EE7B7;")
        col.addWidget(title)
        col.addWidget(self._page_lbl)
        lay.addLayout(col)
        lay.addStretch()

        ver = QLabel(f"v{APP_VER}")
        ver.setStyleSheet("font-size: 12px; color: #334155;")
        lay.addWidget(ver)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor("#0F172A"))
        g.setColorAt(1, QColor("#064E3B"))
        p.fillRect(self.rect(), g)

    def set_page(self, text: str):
        self._page_lbl.setText(text)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 0 — WELCOME
# ══════════════════════════════════════════════════════════════════════════════
class WelcomePage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 28, 40, 20)
        lay.setSpacing(14)

        greet = QLabel(f"Bem-vindo ao {APP_NAME}!")
        greet.setStyleSheet("font-size: 21px; font-weight: 700; color: #0F172A;")
        lay.addWidget(greet)

        desc = QLabel(
            "Este assistente irá guiá-lo pela instalação do URANNIO Finanças.\n"
            "O processo leva menos de um minuto."
        )
        desc.setStyleSheet("font-size: 13px; color: #64748B;")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #E2E8F0; max-height: 1px; border: none;")
        lay.addWidget(sep)

        feat_lbl = QLabel("O que está incluído:")
        feat_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #374151;")
        lay.addWidget(feat_lbl)

        for icon, text in [
            ("🏠", "Dashboard financeiro com gráficos em tempo real"),
            ("💳", "Gestão de transações, contas e categorias"),
            ("🎯", "Orçamentos mensais com alertas de limite"),
            ("📊", "Relatórios e análises visuais detalhadas"),
            ("🤖", "Insights inteligentes com Claude AI"),
            ("🔥", "Sincronização opcional com Firebase"),
            ("👑", "Painel de administração de usuários"),
        ]:
            row = QHBoxLayout()
            ic = QLabel(icon)
            ic.setFixedWidth(26)
            ic.setStyleSheet("font-size: 15px;")
            tx = QLabel(text)
            tx.setStyleSheet("font-size: 12px; color: #374151;")
            row.addWidget(ic)
            row.addWidget(tx)
            row.addStretch()
            lay.addLayout(row)

        lay.addStretch()

        note = QLabel("Clique em  Próximo  para escolher o local de instalação.")
        note.setStyleSheet(
            "font-size: 12px; color: #94A3B8; background: #F8FAFC; "
            "border-radius: 6px; padding: 8px 12px;"
        )
        lay.addWidget(note)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — PATH SELECTION
# ══════════════════════════════════════════════════════════════════════════════
class PathPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 28, 40, 20)
        lay.setSpacing(16)

        title = QLabel("Local de Instalação")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        lay.addWidget(title)

        sub = QLabel("Escolha onde o URANNIO Finanças será instalado:")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        lay.addWidget(sub)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit(DEFAULT_DIR)
        self.path_input.setMinimumHeight(40)
        self.path_input.setStyleSheet(
            "QLineEdit { border: 1.5px solid #E2E8F0; border-radius: 8px; "
            "padding: 0 12px; font-size: 13px; color: #374151; background: white; } "
            "QLineEdit:focus { border-color: #10B981; }"
        )
        btn_browse = QPushButton("📂  Escolher")
        btn_browse.setFixedHeight(40)
        btn_browse.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #374151; border: 1.5px solid #E2E8F0; "
            "border-radius: 8px; font-size: 12px; font-weight: 600; padding: 0 16px; } "
            "QPushButton:hover { background: #E2E8F0; }"
        )
        btn_browse.clicked.connect(self._browse)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(btn_browse)
        lay.addLayout(path_row)

        self.desktop_chk = QCheckBox("Criar atalho na Área de Trabalho")
        self.desktop_chk.setChecked(True)
        self.desktop_chk.setStyleSheet("font-size: 13px; color: #374151;")
        self.startmenu_chk = QCheckBox("Criar atalho no Menu Iniciar")
        self.startmenu_chk.setChecked(True)
        self.startmenu_chk.setStyleSheet("font-size: 13px; color: #374151;")
        lay.addWidget(self.desktop_chk)
        lay.addWidget(self.startmenu_chk)

        lay.addStretch()

        info = QFrame()
        info.setStyleSheet(
            "QFrame { background: #F0FDF4; border: 1px solid #A7F3D0; border-radius: 8px; }"
        )
        il = QHBoxLayout(info)
        il.setContentsMargins(14, 10, 14, 10)
        il.setSpacing(10)
        il.addWidget(QLabel("ℹ️"))
        tx = QLabel("O URANNIO Finanças requer aproximadamente 120 MB de espaço em disco.")
        tx.setStyleSheet("font-size: 12px; color: #065F46;")
        tx.setWordWrap(True)
        il.addWidget(tx, 1)
        lay.addWidget(info)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta", self.path_input.text())
        if path:
            self.path_input.setText(str(Path(path) / APP_NAME))

    def install_dir(self) -> str:
        return self.path_input.text().strip() or DEFAULT_DIR

    def wants_desktop(self) -> bool:
        return self.desktop_chk.isChecked()

    def wants_startmenu(self) -> bool:
        return self.startmenu_chk.isChecked()


# ══════════════════════════════════════════════════════════════════════════════
# INSTALL WORKER
# ══════════════════════════════════════════════════════════════════════════════
class InstallWorker(QThread):
    step_done   = pyqtSignal(int)
    progress    = pyqtSignal(int)
    finished_ok  = pyqtSignal()
    finished_err = pyqtSignal(str)

    STEPS = [
        "Preparando pasta de instalação...",
        "Copiando arquivos do URANNIO...",
        "Criando atalho na Área de Trabalho...",
        "Criando atalho no Menu Iniciar...",
        "Registrando desinstalador no Windows...",
        "Finalizando instalação...",
    ]

    def __init__(self, install_dir: str, desktop: bool, startmenu: bool):
        super().__init__()
        self.install_dir = Path(install_dir)
        self.desktop = desktop
        self.startmenu = startmenu

    def run(self):
        import time
        try:
            # 0 — Create directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self.step_done.emit(0); self.progress.emit(10); time.sleep(0.3)

            # 1 — Copy exe
            src = Path(resource(APP_EXE))
            shutil.copy2(src, self.install_dir / APP_EXE)
            dst_exe = self.install_dir / APP_EXE
            self.step_done.emit(1); self.progress.emit(50); time.sleep(0.2)

            # 2 — Desktop shortcut
            if self.desktop:
                self._shortcut(dst_exe, Path.home() / "Desktop" / f"{APP_NAME}.lnk")
            self.step_done.emit(2); self.progress.emit(65); time.sleep(0.2)

            # 3 — Start Menu shortcut
            if self.startmenu:
                sm = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs"
                sm.mkdir(parents=True, exist_ok=True)
                self._shortcut(dst_exe, sm / f"{APP_NAME}.lnk")
            self.step_done.emit(3); self.progress.emit(78); time.sleep(0.2)

            # 4 — Registry
            self._register(dst_exe)
            self.step_done.emit(4); self.progress.emit(90); time.sleep(0.3)

            # 5 — Done
            time.sleep(0.4)
            self.step_done.emit(5); self.progress.emit(100)
            self.finished_ok.emit()

        except Exception as exc:
            self.finished_err.emit(str(exc))

    def _shortcut(self, target: Path, link: Path):
        ps = (
            f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{link}");'
            f'$s.TargetPath="{target}";'
            f'$s.Description="{APP_NAME}";'
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
        )

    def _register(self, dst_exe: Path):
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY)
            vals = [
                ("DisplayName",     winreg.REG_SZ,    APP_NAME),
                ("DisplayVersion",  winreg.REG_SZ,    APP_VER),
                ("Publisher",       winreg.REG_SZ,    PUBLISHER),
                ("InstallLocation", winreg.REG_SZ,    str(self.install_dir)),
                ("UninstallString", winreg.REG_SZ,    f'"{dst_exe}" --uninstall'),
                ("NoModify",        winreg.REG_DWORD, 1),
                ("NoRepair",        winreg.REG_DWORD, 1),
            ]
            for name, kind, val in vals:
                winreg.SetValueEx(key, name, 0, kind, val)
            winreg.CloseKey(key)
        except Exception:
            pass  # non-fatal


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — INSTALLING
# ══════════════════════════════════════════════════════════════════════════════
class InstallPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 28, 40, 20)
        lay.setSpacing(14)

        self.title = QLabel("Instalando URANNIO Finanças...")
        self.title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        lay.addWidget(self.title)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(12)
        self.bar.setStyleSheet("""
            QProgressBar { background: #E2E8F0; border-radius: 6px; border: none; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #059669, stop:1 #34D399);
                border-radius: 6px;
            }
        """)
        lay.addWidget(self.bar)

        self.pct = QLabel("0%")
        self.pct.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lay.addWidget(self.pct)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #E2E8F0; max-height: 1px; border: none;")
        lay.addWidget(sep)

        self._step_widgets: list[tuple[QLabel, QLabel]] = []
        for text in InstallWorker.STEPS:
            row = QHBoxLayout()
            row.setSpacing(10)
            ic = QLabel("⏸")
            ic.setFixedWidth(22)
            ic.setStyleSheet("font-size: 14px;")
            tx = QLabel(text)
            tx.setStyleSheet("font-size: 12px; color: #CBD5E1;")
            row.addWidget(ic)
            row.addWidget(tx, 1)
            lay.addLayout(row)
            self._step_widgets.append((ic, tx))

        lay.addStretch()

    def set_progress(self, val: int):
        # Animate bar smoothly
        self._anim = QPropertyAnimation(self.bar, b"value")
        self._anim.setDuration(300)
        self._anim.setEndValue(val)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()
        self.pct.setText(f"{val}%")

    def mark_step(self, idx: int):
        if 0 <= idx < len(self._step_widgets):
            ic, tx = self._step_widgets[idx]
            ic.setText("✅")
            tx.setStyleSheet("font-size: 12px; color: #059669; font-weight: 600;")
        # Activate next
        nxt = idx + 1
        if nxt < len(self._step_widgets):
            ic2, tx2 = self._step_widgets[nxt]
            ic2.setText("⏳")
            tx2.setStyleSheet("font-size: 12px; color: #374151;")

    def reset(self):
        self.bar.setValue(0)
        self.pct.setText("0%")
        for ic, tx in self._step_widgets:
            ic.setText("⏸")
            tx.setStyleSheet("font-size: 12px; color: #CBD5E1;")
        if self._step_widgets:
            self._step_widgets[0][0].setText("⏳")
            self._step_widgets[0][1].setStyleSheet("font-size: 12px; color: #374151;")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — FINISH
# ══════════════════════════════════════════════════════════════════════════════
class FinishPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #F0FDF4; border: 2px solid #10B981; border-radius: 16px; }"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(36, 28, 36, 28)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.setSpacing(10)

        if HAS_LOGO:
            logo = AnimatedLogo(size=60)
            cl.addWidget(logo, 0, Qt.AlignmentFlag.AlignCenter)

        check = QLabel("✅")
        check.setStyleSheet("font-size: 44px;")
        check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(check)

        done = QLabel("Instalação Concluída!")
        done.setStyleSheet("font-size: 20px; font-weight: 800; color: #065F46;")
        done.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(done)

        msg = QLabel(
            f"{APP_NAME} foi instalado com sucesso\ne está pronto para uso."
        )
        msg.setStyleSheet("font-size: 13px; color: #059669;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        cl.addWidget(msg)

        lay.addWidget(card)

        self.launch_chk = QCheckBox(f"Iniciar {APP_NAME} agora")
        self.launch_chk.setChecked(True)
        self.launch_chk.setStyleSheet("font-size: 13px; color: #374151;")
        lay.addWidget(self.launch_chk, 0, Qt.AlignmentFlag.AlignCenter)

    def wants_launch(self) -> bool:
        return self.launch_chk.isChecked()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN INSTALLER WINDOW
# ══════════════════════════════════════════════════════════════════════════════
_PAGE_LABELS = ["Bem-vindo", "Local de Instalação", "Instalando...", "Concluído"]
_BTN_LABELS  = ["Próximo  →", "Instalar  →", "", "Fechar"]


class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Instalador — {APP_NAME} v{APP_VER}")
        self.setFixedSize(700, 540)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint
        )
        self._install_dir = DEFAULT_DIR
        self._build_ui()
        self._go(0)
        self._center()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self.header = Header()
        rl.addWidget(self.header)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #1E3A2F; border: none;")
        rl.addWidget(div)

        self.stack = QStackedWidget()
        rl.addWidget(self.stack, 1)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(64)
        footer.setStyleSheet(
            "QFrame { background: #F8FAFC; border-top: 1px solid #E2E8F0; }"
        )
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(32, 0, 32, 0)
        fl.setSpacing(10)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFixedSize(100, 36)
        self.btn_cancel.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #64748B; border: 1px solid #E2E8F0; "
            "border-radius: 8px; font-size: 13px; } "
            "QPushButton:hover { background: #E2E8F0; }"
        )
        self.btn_cancel.clicked.connect(self.close)

        self.btn_next = QPushButton("Próximo  →")
        self.btn_next.setFixedSize(130, 36)
        self.btn_next.setStyleSheet(
            "QPushButton { background: #059669; color: white; border: none; "
            "border-radius: 8px; font-size: 13px; font-weight: 700; } "
            "QPushButton:hover { background: #047857; } "
            "QPushButton:disabled { background: #D1FAE5; color: #6EE7B7; }"
        )
        self.btn_next.clicked.connect(self._next)

        fl.addStretch()
        fl.addWidget(self.btn_cancel)
        fl.addWidget(self.btn_next)
        rl.addWidget(footer)

        # Pages
        self.p_welcome = WelcomePage()
        self.p_path    = PathPage()
        self.p_install = InstallPage()
        self.p_finish  = FinishPage()
        for p in [self.p_welcome, self.p_path, self.p_install, self.p_finish]:
            self.stack.addWidget(p)

    def _go(self, idx: int):
        self._fade_to(idx)
        self.header.set_page(_PAGE_LABELS[idx])
        self.btn_next.setText(_BTN_LABELS[idx])
        self.btn_next.setVisible(bool(_BTN_LABELS[idx]))
        self.btn_next.setEnabled(idx != 2)
        self.btn_cancel.setVisible(idx < 3)

    def _fade_to(self, idx: int):
        old = self.stack.currentWidget()
        eff = QGraphicsOpacityEffect(old)
        old.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(120)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InQuad)

        def _switch():
            self.stack.setCurrentIndex(idx)
            new = self.stack.currentWidget()
            eff2 = QGraphicsOpacityEffect(new)
            new.setGraphicsEffect(eff2)
            anim2 = QPropertyAnimation(eff2, b"opacity", self)
            anim2.setDuration(180)
            anim2.setStartValue(0.0)
            anim2.setEndValue(1.0)
            anim2.setEasingCurve(QEasingCurve.Type.OutQuad)
            anim2.start()

        anim.finished.connect(_switch)
        anim.start()

    def _next(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self._go(1)
        elif idx == 1:
            if not is_admin():
                elevate()
                return
            self._install_dir = self.p_path.install_dir()
            self.p_install.reset()
            self._go(2)
            self._run_install()
        elif idx == 3:
            if self.p_finish.wants_launch():
                exe = Path(self._install_dir) / APP_EXE
                if exe.exists():
                    subprocess.Popen([str(exe)])
            self.close()

    def _run_install(self):
        self._worker = InstallWorker(
            self._install_dir,
            self.p_path.wants_desktop(),
            self.p_path.wants_startmenu(),
        )
        self._worker.step_done.connect(self.p_install.mark_step)
        self._worker.progress.connect(self.p_install.set_progress)
        self._worker.finished_ok.connect(lambda: self._go(3))
        self._worker.finished_err.connect(self._on_error)
        self._worker.start()

    def _on_error(self, err: str):
        QMessageBox.critical(self, "Erro na instalação",
                             f"Ocorreu um erro durante a instalação:\n\n{err}")
        self._go(0)

    def _center(self):
        g = QApplication.primaryScreen().geometry()
        self.move((g.width() - self.width()) // 2, (g.height() - self.height()) // 2)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VER)
    app.setStyle("Fusion")

    splash = SplashScreen()
    splash.show()

    win = InstallerWindow()

    def _show_main():
        splash.close()
        win.show()

    splash.finished.connect(_show_main)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
