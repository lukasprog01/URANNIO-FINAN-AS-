import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path


def _app_data_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home()))
    d = base / "URANNIO Finanças"
    d.mkdir(parents=True, exist_ok=True)
    return d


_DEFAULT_DB = str(_app_data_dir() / "finance_control.db")


class Database:
    def __init__(self, db_path=_DEFAULT_DB):
        self.db_path = db_path
        self._firebase = None   # set via set_firebase_manager()

    def set_firebase_manager(self, fm):
        self._firebase = fm

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    must_change_password INTEGER DEFAULT 0,
                    temp_password_hash TEXT,
                    temp_password_salt TEXT,
                    temp_password_expiry TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    balance REAL DEFAULT 0.0,
                    color TEXT DEFAULT '#3B82F6',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    color TEXT DEFAULT '#3B82F6',
                    icon TEXT DEFAULT '💰',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    account_id INTEGER,
                    category_id INTEGER,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                );

                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(user_id, category_id, month, year),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                );
            """)
        self._migrate()

    def _migrate(self):
        """Add columns introduced in newer versions to existing databases."""
        new_cols = [
            ("role",                 "TEXT DEFAULT 'user'"),
            ("must_change_password", "INTEGER DEFAULT 0"),
            ("temp_password_hash",   "TEXT"),
            ("temp_password_salt",   "TEXT"),
            ("temp_password_expiry", "TEXT"),
        ]
        with self.get_connection() as conn:
            existing = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
            for col, definition in new_cols:
                if col not in existing:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")

    # ── Firebase shorthand ──────────────────────────────────────────────────────

    def _fb_sync(self, user_id: int, collection: str, doc_id: int, data: dict):
        if self._firebase:
            self._firebase.sync(user_id, collection, doc_id, data)

    def _fb_delete(self, user_id: int, collection: str, doc_id: int):
        if self._firebase:
            self._firebase.delete(user_id, collection, doc_id)

    # ── Authentication ──────────────────────────────────────────────────────────

    def _hash_password(self, password: str, salt: str = None):
        if salt is None:
            salt = secrets.token_hex(32)
        hashed = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return hashed, salt

    def get_user_count(self) -> int:
        with self.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create_user(self, username: str, email: str, password: str) -> dict:
        role = "admin" if self.get_user_count() == 0 else "user"
        password_hash, salt = self._hash_password(password)
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
                    (username, email, password_hash, salt, role),
                )
                user_id = cursor.lastrowid
                self._create_default_categories(conn, user_id)
                conn.execute(
                    "INSERT INTO accounts (user_id, name, type, balance, color) VALUES (?, ?, ?, ?, ?)",
                    (user_id, "Conta Corrente", "checking", 0.0, "#3B82F6"),
                )
                return {"success": True, "user_id": user_id, "role": role}
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return {"success": False, "error": "Nome de usuário já existe"}
            elif "email" in str(e):
                return {"success": False, "error": "E-mail já cadastrado"}
            return {"success": False, "error": str(e)}

    def _create_default_categories(self, conn, user_id: int):
        income = [
            ("Salário", "#10B981", "💼"),
            ("Freelance", "#06B6D4", "💻"),
            ("Investimentos", "#8B5CF6", "📈"),
            ("Outros", "#6B7280", "💰"),
        ]
        expense = [
            ("Alimentação", "#F97316", "🍔"),
            ("Transporte", "#3B82F6", "🚗"),
            ("Moradia", "#8B5CF6", "🏠"),
            ("Saúde", "#EF4444", "💊"),
            ("Educação", "#06B6D4", "📚"),
            ("Lazer", "#F59E0B", "🎭"),
            ("Vestuário", "#EC4899", "👕"),
            ("Outros", "#6B7280", "💸"),
        ]
        for name, color, icon in income:
            conn.execute(
                "INSERT INTO categories (user_id, name, type, color, icon) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, "income", color, icon),
            )
        for name, color, icon in expense:
            conn.execute(
                "INSERT INTO categories (user_id, name, type, color, icon) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, "expense", color, icon),
            )

    def authenticate_user(self, username: str, password: str) -> dict:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (username, username),
            ).fetchone()
            if not row:
                return {"success": False, "error": "Usuário não encontrado"}
            pwd_hash, _ = self._hash_password(password, row["salt"])
            if pwd_hash == row["password_hash"]:
                return {"success": True, "user": dict(row)}
            # Check temporary password
            if row["temp_password_hash"] and row["temp_password_expiry"]:
                from datetime import datetime
                try:
                    expiry = datetime.strptime(row["temp_password_expiry"], "%Y-%m-%d %H:%M:%S")
                    if datetime.now() <= expiry:
                        tmp_hash, _ = self._hash_password(password, row["temp_password_salt"])
                        if tmp_hash == row["temp_password_hash"]:
                            return {"success": True, "user": dict(row)}
                except Exception:
                    pass
            return {"success": False, "error": "Senha incorreta"}

    # ── Admin / user management ─────────────────────────────────────────────────

    def get_user_by_email(self, email: str) -> dict | None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            return dict(row) if row else None

    def get_all_users(self) -> list:
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT id, username, email, role, created_at, must_change_password FROM users ORDER BY id"
            ).fetchall()]

    def is_admin(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            row = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
            return bool(row and row["role"] == "admin")

    def set_user_role(self, user_id: int, role: str) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
            return True
        except Exception:
            return False

    def delete_user_admin(self, user_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
                conn.execute("DELETE FROM budgets WHERE user_id=?", (user_id,))
                conn.execute("DELETE FROM categories WHERE user_id=?", (user_id,))
                conn.execute("DELETE FROM accounts WHERE user_id=?", (user_id,))
                conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            return True
        except Exception:
            return False

    def set_temp_password(self, user_id: int, temp_password: str) -> bool:
        from datetime import datetime, timedelta
        expiry = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        tmp_hash, salt = self._hash_password(temp_password)
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """UPDATE users
                       SET temp_password_hash=?, temp_password_salt=?,
                           temp_password_expiry=?, must_change_password=1
                       WHERE id=?""",
                    (tmp_hash, salt, expiry, user_id),
                )
            return True
        except Exception:
            return False

    def change_password(self, user_id: int, new_password: str) -> bool:
        new_hash, salt = self._hash_password(new_password)
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """UPDATE users
                       SET password_hash=?, salt=?,
                           temp_password_hash=NULL, temp_password_salt=NULL,
                           temp_password_expiry=NULL, must_change_password=0
                       WHERE id=?""",
                    (new_hash, salt, user_id),
                )
            return True
        except Exception:
            return False

    # ── Accounts ────────────────────────────────────────────────────────────────

    def get_accounts(self, user_id: int) -> list:
        with self.get_connection() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM accounts WHERE user_id = ? ORDER BY name",
                    (user_id,),
                ).fetchall()
            ]

    def create_account(self, user_id, name, acct_type, balance, color) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO accounts (user_id, name, type, balance, color) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, acct_type, balance, color),
                )
                new_id = cursor.lastrowid
            self._fb_sync(user_id, "accounts", new_id, {
                "id": new_id, "user_id": user_id, "name": name,
                "type": acct_type, "balance": balance, "color": color,
            })
            return True
        except Exception:
            return False

    def update_account(self, account_id, name, acct_type, balance, color) -> bool:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM accounts WHERE id=?", (account_id,)
                ).fetchone()
                user_id = row["user_id"] if row else None
                conn.execute(
                    "UPDATE accounts SET name=?, type=?, balance=?, color=? WHERE id=?",
                    (name, acct_type, balance, color, account_id),
                )
            if user_id:
                self._fb_sync(user_id, "accounts", account_id, {
                    "id": account_id, "user_id": user_id, "name": name,
                    "type": acct_type, "balance": balance, "color": color,
                })
            return True
        except Exception:
            return False

    def delete_account(self, account_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM accounts WHERE id=?", (account_id,)
                ).fetchone()
                user_id = row["user_id"] if row else None
                conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
            if user_id:
                self._fb_delete(user_id, "accounts", account_id)
            return True
        except Exception:
            return False

    def get_total_balance(self, user_id: int) -> float:
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE user_id=?",
                (user_id,),
            ).fetchone()
            return result[0] if result else 0.0

    # ── Categories ──────────────────────────────────────────────────────────────

    def get_categories(self, user_id: int, cat_type: str = None) -> list:
        with self.get_connection() as conn:
            if cat_type:
                rows = conn.execute(
                    "SELECT * FROM categories WHERE user_id=? AND type=? ORDER BY name",
                    (user_id, cat_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM categories WHERE user_id=? ORDER BY type, name",
                    (user_id,),
                ).fetchall()
            return [dict(r) for r in rows]

    def create_category(self, user_id, name, cat_type, color, icon) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO categories (user_id, name, type, color, icon) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, cat_type, color, icon),
                )
                new_id = cursor.lastrowid
            self._fb_sync(user_id, "categories", new_id, {
                "id": new_id, "user_id": user_id, "name": name,
                "type": cat_type, "color": color, "icon": icon,
            })
            return True
        except Exception:
            return False

    def update_category(self, category_id, name, cat_type, color, icon) -> bool:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM categories WHERE id=?", (category_id,)
                ).fetchone()
                user_id = row["user_id"] if row else None
                conn.execute(
                    "UPDATE categories SET name=?, type=?, color=?, icon=? WHERE id=?",
                    (name, cat_type, color, icon, category_id),
                )
            if user_id:
                self._fb_sync(user_id, "categories", category_id, {
                    "id": category_id, "user_id": user_id, "name": name,
                    "type": cat_type, "color": color, "icon": icon,
                })
            return True
        except Exception:
            return False

    def delete_category(self, category_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM categories WHERE id=?", (category_id,)
                ).fetchone()
                user_id = row["user_id"] if row else None
                conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
            if user_id:
                self._fb_delete(user_id, "categories", category_id)
            return True
        except Exception:
            return False

    # ── Transactions ────────────────────────────────────────────────────────────

    def get_transactions(
        self,
        user_id: int,
        month: int = None,
        year: int = None,
        account_id: int = None,
        category_id: int = None,
        trans_type: str = None,
        limit: int = None,
    ) -> list:
        query = """
            SELECT t.*,
                   a.name as account_name, a.color as account_color,
                   c.name as category_name, c.color as category_color, c.icon as category_icon
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
        """
        params = [user_id]

        if month and year:
            query += " AND strftime('%m', t.date)=? AND strftime('%Y', t.date)=?"
            params.extend([f"{month:02d}", str(year)])
        elif year:
            query += " AND strftime('%Y', t.date)=?"
            params.append(str(year))

        if account_id:
            query += " AND t.account_id=?"
            params.append(account_id)
        if category_id:
            query += " AND t.category_id=?"
            params.append(category_id)
        if trans_type:
            query += " AND t.type=?"
            params.append(trans_type)

        query += " ORDER BY t.date DESC, t.created_at DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def create_transaction(
        self, user_id, account_id, category_id, trans_type, amount, description, date, notes=None
    ) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO transactions
                       (user_id, account_id, category_id, type, amount, description, date, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, account_id, category_id, trans_type, amount, description, date, notes),
                )
                new_id = cursor.lastrowid
                if account_id:
                    if trans_type == "income":
                        conn.execute(
                            "UPDATE accounts SET balance = balance + ? WHERE id=?",
                            (amount, account_id),
                        )
                    elif trans_type == "expense":
                        conn.execute(
                            "UPDATE accounts SET balance = balance - ? WHERE id=?",
                            (amount, account_id),
                        )
            self._fb_sync(user_id, "transactions", new_id, {
                "id": new_id, "user_id": user_id, "account_id": account_id,
                "category_id": category_id, "type": trans_type, "amount": amount,
                "description": description, "date": date, "notes": notes,
            })
            return True
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return False

    def update_transaction(
        self, transaction_id, account_id, category_id, trans_type, amount, description, date, notes=None
    ) -> bool:
        try:
            user_id = None
            with self.get_connection() as conn:
                old = conn.execute(
                    "SELECT * FROM transactions WHERE id=?", (transaction_id,)
                ).fetchone()
                if old:
                    user_id = old["user_id"]
                    if old["account_id"]:
                        if old["type"] == "income":
                            conn.execute(
                                "UPDATE accounts SET balance = balance - ? WHERE id=?",
                                (old["amount"], old["account_id"]),
                            )
                        elif old["type"] == "expense":
                            conn.execute(
                                "UPDATE accounts SET balance = balance + ? WHERE id=?",
                                (old["amount"], old["account_id"]),
                            )
                conn.execute(
                    """UPDATE transactions SET account_id=?, category_id=?, type=?,
                       amount=?, description=?, date=?, notes=? WHERE id=?""",
                    (account_id, category_id, trans_type, amount, description, date, notes, transaction_id),
                )
                if account_id:
                    if trans_type == "income":
                        conn.execute(
                            "UPDATE accounts SET balance = balance + ? WHERE id=?",
                            (amount, account_id),
                        )
                    elif trans_type == "expense":
                        conn.execute(
                            "UPDATE accounts SET balance = balance - ? WHERE id=?",
                            (amount, account_id),
                        )
            if user_id:
                self._fb_sync(user_id, "transactions", transaction_id, {
                    "id": transaction_id, "user_id": user_id, "account_id": account_id,
                    "category_id": category_id, "type": trans_type, "amount": amount,
                    "description": description, "date": date, "notes": notes,
                })
            return True
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False

    def delete_transaction(self, transaction_id: int) -> bool:
        try:
            user_id = None
            with self.get_connection() as conn:
                old = conn.execute(
                    "SELECT * FROM transactions WHERE id=?", (transaction_id,)
                ).fetchone()
                if old:
                    user_id = old["user_id"]
                    if old["account_id"]:
                        if old["type"] == "income":
                            conn.execute(
                                "UPDATE accounts SET balance = balance - ? WHERE id=?",
                                (old["amount"], old["account_id"]),
                            )
                        elif old["type"] == "expense":
                            conn.execute(
                                "UPDATE accounts SET balance = balance + ? WHERE id=?",
                                (old["amount"], old["account_id"]),
                            )
                conn.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
            if user_id:
                self._fb_delete(user_id, "transactions", transaction_id)
            return True
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False

    # ── Reports ─────────────────────────────────────────────────────────────────

    def get_monthly_summary(self, user_id: int, month: int, year: int) -> dict:
        with self.get_connection() as conn:
            r = conn.execute(
                """SELECT
                       SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income,
                       SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                   FROM transactions
                   WHERE user_id=? AND strftime('%m', date)=? AND strftime('%Y', date)=?""",
                (user_id, f"{month:02d}", str(year)),
            ).fetchone()
            income = r["income"] or 0.0
            expense = r["expense"] or 0.0
            return {"income": income, "expense": expense, "balance": income - expense}

    def get_transaction_count(self, user_id: int) -> int:
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id=?", (user_id,)
            ).fetchone()
            return result[0] if result else 0

    def get_transaction_months(self, user_id: int) -> int:
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT COUNT(DISTINCT strftime('%Y-%m', date)) FROM transactions WHERE user_id=?",
                (user_id,),
            ).fetchone()
            return result[0] if result else 0

    def get_expense_by_category(self, user_id: int, month: int, year: int) -> list:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT c.name, c.color, c.icon, SUM(t.amount) as total
                   FROM transactions t JOIN categories c ON t.category_id = c.id
                   WHERE t.user_id=? AND t.type='expense'
                     AND strftime('%m', t.date)=? AND strftime('%Y', t.date)=?
                   GROUP BY c.id ORDER BY total DESC""",
                (user_id, f"{month:02d}", str(year)),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_income_by_category(self, user_id: int, month: int, year: int) -> list:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT c.name, c.color, c.icon, SUM(t.amount) as total
                   FROM transactions t JOIN categories c ON t.category_id = c.id
                   WHERE t.user_id=? AND t.type='income'
                     AND strftime('%m', t.date)=? AND strftime('%Y', t.date)=?
                   GROUP BY c.id ORDER BY total DESC""",
                (user_id, f"{month:02d}", str(year)),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_yearly_summary(self, user_id: int, year: int) -> list:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT
                       CAST(strftime('%m', date) AS INTEGER) as month,
                       SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income,
                       SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                   FROM transactions
                   WHERE user_id=? AND strftime('%Y', date)=?
                   GROUP BY month ORDER BY month""",
                (user_id, str(year)),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Budgets ─────────────────────────────────────────────────────────────────

    def get_budgets(self, user_id: int, month: int, year: int) -> list:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT b.*, c.name as category_name, c.color, c.icon,
                          COALESCE(
                              (SELECT SUM(t.amount) FROM transactions t
                               WHERE t.category_id = b.category_id
                                 AND t.user_id = b.user_id
                                 AND t.type = 'expense'
                                 AND strftime('%m', t.date) = ?
                                 AND strftime('%Y', t.date) = ?), 0
                          ) as spent
                   FROM budgets b JOIN categories c ON b.category_id = c.id
                   WHERE b.user_id=? AND b.month=? AND b.year=?""",
                (f"{month:02d}", str(year), user_id, month, year),
            ).fetchall()
            return [dict(r) for r in rows]

    def save_budget(self, user_id, category_id, amount, month, year) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO budgets (user_id, category_id, amount, month, year)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(user_id, category_id, month, year)
                       DO UPDATE SET amount=excluded.amount""",
                    (user_id, category_id, amount, month, year),
                )
                new_id = cursor.lastrowid
            self._fb_sync(user_id, "budgets", new_id, {
                "id": new_id, "user_id": user_id, "category_id": category_id,
                "amount": amount, "month": month, "year": year,
            })
            return True
        except Exception:
            return False

    def delete_budget(self, budget_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM budgets WHERE id=?", (budget_id,)
                ).fetchone()
                user_id = row["user_id"] if row else None
                conn.execute("DELETE FROM budgets WHERE id=?", (budget_id,))
            if user_id:
                self._fb_delete(user_id, "budgets", budget_id)
            return True
        except Exception:
            return False
