import json
import os
from pathlib import Path


def _app_data_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home()))
    d = base / "URANNIO Finanças"
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_FILE = str(_app_data_dir() / "app_config.json")


class ConfigManager:
    def __init__(self):
        self.config = self._load()

    def _load(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default()

    def _default(self) -> dict:
        return {
            "firebase": {
                "enabled": False,
                "credentials_path": "",
                "auto_sync": True,
            },
            "ai": {
                "api_key": "",
                "model": "claude-haiku-4-5-20251001",
            },
            "email": {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "use_tls": True,
            },
        }

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")

    # ── Firebase helpers ───────────────────────────────────────────────────────

    @property
    def firebase_enabled(self) -> bool:
        return self.config.get("firebase", {}).get("enabled", False)

    @firebase_enabled.setter
    def firebase_enabled(self, value: bool):
        self.config.setdefault("firebase", {})["enabled"] = value
        self.save()

    @property
    def firebase_credentials_path(self) -> str:
        return self.config.get("firebase", {}).get("credentials_path", "")

    @firebase_credentials_path.setter
    def firebase_credentials_path(self, path: str):
        self.config.setdefault("firebase", {})["credentials_path"] = path
        self.save()

    @property
    def firebase_auto_sync(self) -> bool:
        return self.config.get("firebase", {}).get("auto_sync", True)

    @firebase_auto_sync.setter
    def firebase_auto_sync(self, value: bool):
        self.config.setdefault("firebase", {})["auto_sync"] = value
        self.save()

    # ── AI helpers ─────────────────────────────────────────────────────────────

    @property
    def ai_api_key(self) -> str:
        return self.config.get("ai", {}).get("api_key", "")

    @ai_api_key.setter
    def ai_api_key(self, value: str):
        self.config.setdefault("ai", {})["api_key"] = value
        self.save()

    @property
    def ai_model(self) -> str:
        return self.config.get("ai", {}).get("model", "claude-haiku-4-5-20251001")

    @ai_model.setter
    def ai_model(self, value: str):
        self.config.setdefault("ai", {})["model"] = value
        self.save()

    # ── Email helpers ──────────────────────────────────────────────────────────

    @property
    def email_smtp_host(self) -> str:
        return self.config.get("email", {}).get("smtp_host", "smtp.gmail.com")

    @email_smtp_host.setter
    def email_smtp_host(self, v: str):
        self.config.setdefault("email", {})["smtp_host"] = v
        self.save()

    @property
    def email_smtp_port(self) -> int:
        return self.config.get("email", {}).get("smtp_port", 587)

    @email_smtp_port.setter
    def email_smtp_port(self, v: int):
        self.config.setdefault("email", {})["smtp_port"] = v
        self.save()

    @property
    def email_sender(self) -> str:
        return self.config.get("email", {}).get("sender_email", "")

    @email_sender.setter
    def email_sender(self, v: str):
        self.config.setdefault("email", {})["sender_email"] = v
        self.save()

    @property
    def email_password(self) -> str:
        return self.config.get("email", {}).get("sender_password", "")

    @email_password.setter
    def email_password(self, v: str):
        self.config.setdefault("email", {})["sender_password"] = v
        self.save()

    @property
    def email_use_tls(self) -> bool:
        return self.config.get("email", {}).get("use_tls", True)

    @email_use_tls.setter
    def email_use_tls(self, v: bool):
        self.config.setdefault("email", {})["use_tls"] = v
        self.save()
