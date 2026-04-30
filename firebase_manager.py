import threading
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class _Signals(QObject):
    """Qt signal carrier — lives on the main thread so cross-thread emits are queued safely."""
    status_changed = pyqtSignal(str, str)   # (status_key, message)
    # status_key: "connected" | "disconnected" | "syncing" | "synced" | "error"


class FirebaseManager:
    """
    Singleton that wraps Firebase Admin SDK operations.
    All Firestore writes run in daemon threads so they never block the UI.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                obj._ready = False
                cls._instance = obj
        return cls._instance

    def __init__(self):
        if self._ready:
            return
        self.signals = _Signals()
        self.app = None
        self.firestore_db = None
        self.is_connected = False
        self.auto_sync = True
        self.last_sync: datetime | None = None
        self._sync_lock = threading.Lock()
        self._ready = True

    # ── Connection ─────────────────────────────────────────────────────────────

    def connect(self, credentials_path: str) -> dict:
        try:
            import firebase_admin
            from firebase_admin import credentials as fb_creds, firestore

            with self._sync_lock:
                try:
                    if firebase_admin._apps:
                        firebase_admin.delete_app(firebase_admin.get_app())
                except Exception:
                    pass

                cred = fb_creds.Certificate(credentials_path)
                self.app = firebase_admin.initialize_app(cred)
                self.firestore_db = firestore.client()
                self.is_connected = True

            self.signals.status_changed.emit("connected", "Firebase conectado com sucesso!")
            return {"success": True}

        except ImportError:
            msg = "Pacote firebase-admin não instalado.\nAbra o terminal e execute:\n\npip install firebase-admin"
            self.is_connected = False
            self.signals.status_changed.emit("error", msg)
            return {"success": False, "error": msg}
        except Exception as e:
            self.is_connected = False
            self.signals.status_changed.emit("error", str(e))
            return {"success": False, "error": str(e)}

    def disconnect(self):
        try:
            import firebase_admin
            with self._sync_lock:
                if firebase_admin._apps:
                    firebase_admin.delete_app(firebase_admin.get_app())
        except Exception:
            pass
        self.app = None
        self.firestore_db = None
        self.is_connected = False
        self.signals.status_changed.emit("disconnected", "Firebase desconectado.")

    # ── Internal helpers ────────────────────────────────────────────────────────

    def _col(self, user_id: int, collection: str):
        return (
            self.firestore_db
            .collection("financecontrol")
            .document(str(user_id))
            .collection(collection)
        )

    def _write(self, user_id: int, collection: str, doc_id: int, data: dict):
        """Blocking write — call from background thread only."""
        if not self.is_connected or not self.auto_sync:
            return
        try:
            clean = {k: v for k, v in data.items() if v is not None}
            with self._sync_lock:
                self._col(user_id, collection).document(str(doc_id)).set(clean)
            self.last_sync = datetime.now()
            ts = self.last_sync.strftime("%H:%M:%S")
            self.signals.status_changed.emit("synced", f"Sincronizado às {ts}")
        except Exception as e:
            self.signals.status_changed.emit("error", f"Erro de sync: {e}")

    def _erase(self, user_id: int, collection: str, doc_id: int):
        """Blocking delete — call from background thread only."""
        if not self.is_connected or not self.auto_sync:
            return
        try:
            with self._sync_lock:
                self._col(user_id, collection).document(str(doc_id)).delete()
            self.last_sync = datetime.now()
        except Exception as e:
            self.signals.status_changed.emit("error", f"Erro ao deletar: {e}")

    # ── Non-blocking public API ─────────────────────────────────────────────────

    def sync(self, user_id: int, collection: str, doc_id: int, data: dict):
        if not self.is_connected or not self.auto_sync:
            return
        self.signals.status_changed.emit("syncing", "Sincronizando...")
        threading.Thread(
            target=self._write,
            args=(user_id, collection, doc_id, data),
            daemon=True,
        ).start()

    def delete(self, user_id: int, collection: str, doc_id: int):
        if not self.is_connected or not self.auto_sync:
            return
        threading.Thread(
            target=self._erase,
            args=(user_id, collection, doc_id),
            daemon=True,
        ).start()

    # ── Full sync ───────────────────────────────────────────────────────────────

    def sync_all(self, local_db, user_id: int):
        """Push entire local DB to Firestore — runs in background thread."""
        if not self.is_connected:
            return
        self.signals.status_changed.emit("syncing", "Sincronização completa em progresso...")
        threading.Thread(
            target=self._sync_all_blocking,
            args=(local_db, user_id),
            daemon=True,
        ).start()

    def _sync_all_blocking(self, local_db, user_id: int):
        counts = {}
        try:
            accts = local_db.get_accounts(user_id)
            for acct in accts:
                self._write(user_id, "accounts", acct["id"], dict(acct))
            counts["contas"] = len(accts)

            cats = local_db.get_categories(user_id)
            for cat in cats:
                self._write(user_id, "categories", cat["id"], dict(cat))
            counts["categorias"] = len(cats)

            trans_list = local_db.get_transactions(user_id)
            for trans in trans_list:
                self._write(user_id, "transactions", trans["id"], dict(trans))
            counts["transações"] = len(trans_list)

            for bgt in local_db.get_budgets(user_id, datetime.now().month, datetime.now().year):
                self._write(user_id, "budgets", bgt["id"], dict(bgt))

            self.last_sync = datetime.now()
            ts = self.last_sync.strftime("%H:%M:%S")
            summary = ", ".join(f"{v} {k}" for k, v in counts.items())
            self.signals.status_changed.emit("synced", f"Tudo sincronizado às {ts} — {summary}")
        except Exception as e:
            self.signals.status_changed.emit("error", f"Erro na sincronização: {e}")
