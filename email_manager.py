import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailManager:
    def __init__(self, smtp_host: str, smtp_port: int,
                 sender_email: str, sender_password: str, use_tls: bool = True):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls

    def _connect(self):
        ctx = ssl.create_default_context()
        if self.use_tls:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            server.starttls(context=ctx)
        else:
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ctx, timeout=10)
        server.login(self.sender_email, self.sender_password)
        return server

    def test_connection(self) -> dict:
        try:
            with self._connect():
                pass
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_temp_password(self, to_email: str, username: str, temp_password: str) -> dict:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "URANNIO — Sua senha temporária"
            msg["From"]    = f"URANNIO <{self.sender_email}>"
            msg["To"]      = to_email

            html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#0F172A;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:480px;margin:0 auto;background:#1E293B;border-radius:16px;overflow:hidden;">

    <div style="padding:32px;text-align:center;background:linear-gradient(135deg,#065F46,#047857);">
      <div style="font-size:52px;margin-bottom:8px;">💰</div>
      <h1 style="color:#fff;margin:0;font-size:28px;font-weight:800;letter-spacing:8px;">URANNIO</h1>
      <p style="color:#A7F3D0;margin:6px 0 0;font-size:13px;">Controle Financeiro</p>
    </div>

    <div style="padding:32px;">
      <h2 style="color:#F8FAFC;font-size:18px;margin:0 0 12px;">Olá, {username}!</h2>
      <p style="color:#94A3B8;font-size:14px;line-height:1.7;margin:0 0 24px;">
        Recebemos uma solicitação de recuperação de senha para sua conta.
        Use a senha temporária abaixo para acessar o sistema:
      </p>

      <div style="background:#064E3B;border:2px solid #10B981;border-radius:12px;
                  padding:24px;text-align:center;margin:0 0 24px;">
        <p style="color:#6EE7B7;font-size:11px;font-weight:700;margin:0 0 10px;
                  letter-spacing:2px;text-transform:uppercase;">Senha Temporária</p>
        <code style="color:#34D399;font-size:30px;font-weight:800;letter-spacing:6px;">
          {temp_password}
        </code>
      </div>

      <div style="background:#431407;border:1px solid #EA580C;border-radius:8px;
                  padding:14px;margin:0 0 20px;">
        <p style="color:#FED7AA;font-size:13px;margin:0;">
          ⚠️ <strong>Esta senha expira em 24 horas.</strong>
          Após o login, você será solicitado a definir uma nova senha permanente.
        </p>
      </div>

      <p style="color:#475569;font-size:12px;margin:0;">
        Se você não solicitou a recuperação de senha, ignore este e-mail.
        Sua senha atual permanece inalterada.
      </p>
    </div>

    <div style="background:#0F172A;padding:16px;text-align:center;border-top:1px solid #1E293B;">
      <p style="color:#475569;font-size:11px;margin:0;">© 2025 URANNIO — Controle Financeiro</p>
    </div>
  </div>
</body>
</html>"""

            plain = (
                f"URANNIO — Recuperação de Senha\n\n"
                f"Olá, {username}!\n\n"
                f"Sua senha temporária: {temp_password}\n\n"
                f"Esta senha expira em 24 horas. Após o login, defina uma nova senha.\n\n"
                f"Se não solicitou isso, ignore este e-mail.\n\n— Equipe URANNIO"
            )

            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html, "html"))

            with self._connect() as server:
                server.sendmail(self.sender_email, to_email, msg.as_string())

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
