from datetime import datetime, date
import calendar
from PyQt6.QtCore import QThread, pyqtSignal


MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

SYSTEM_PROMPT = """Você é um assistente financeiro pessoal especializado em análise de dados financeiros brasileiros.

Ao analisar os dados, você deve:
- Identificar padrões específicos e concretos presentes nos dados
- Calcular percentuais e variações quando relevante
- Dar recomendações acionáveis com valores estimados em reais (R$)
- Considerar o contexto econômico brasileiro
- Ser direto e objetivo, sem falar de forma genérica

Formate sempre suas respostas com:
- Seções bem definidas com emojis como marcadores visuais
- Bullet points (•) para listas
- Números e percentuais em destaque
- Uma seção final com "🎯 AÇÕES RECOMENDADAS" contendo 3-5 itens prioritários ordenados por impacto

Escreva APENAS em português brasileiro."""

ANALYSIS_PROMPTS = {
    "spending": (
        "📊 ANÁLISE DE GASTOS",
        "Analise detalhadamente os padrões dos meus gastos. "
        "Identifique: (1) categorias onde gasto mais do que deveria, "
        "(2) tendências de aumento ou redução nos últimos meses, "
        "(3) comportamentos financeiros que podem ser prejudiciais a longo prazo. "
        "Use os dados de cada mês para embasar suas conclusões.",
    ),
    "prediction": (
        "📈 PREVISÃO FINANCEIRA",
        "Com base no meu histórico, faça uma previsão detalhada para os próximos 3 meses. "
        "Estime: (1) receitas e despesas esperadas por mês, "
        "(2) saldo projetado ao final de cada mês, "
        "(3) quais categorias de despesa tendem a aumentar e por quê, "
        "(4) em quanto tempo posso atingir uma reserva de emergência de 3 meses de despesas. "
        "Apresente os valores em R$ com base nas médias observadas.",
    ),
    "savings": (
        "💡 OPORTUNIDADES DE ECONOMIA",
        "Identifique todas as oportunidades de economia nos meus dados. "
        "Para cada oportunidade: indique a categoria, o valor mensal que poderia economizar, "
        "e uma ação concreta para implementar. "
        "Priorize as oportunidades de maior impacto financeiro. "
        "Calcule o potencial de economia anual total se eu seguir todas as recomendações.",
    ),
    "health": (
        "🎯 SAÚDE FINANCEIRA",
        "Faça uma avaliação completa da minha saúde financeira. "
        "Inclua: (1) uma nota de 0 a 10 com justificativa, "
        "(2) análise da relação receita/despesa (índice de poupança), "
        "(3) diversificação das fontes de renda, "
        "(4) exposição a riscos financeiros, "
        "(5) comparação com benchmarks saudáveis (ex: regra 50-30-20). "
        "Seja honesto sobre pontos negativos.",
    ),
    "longterm": (
        "🔮 PROJEÇÃO DE LONGO PRAZO",
        "Faça uma análise de longo prazo (1, 3 e 5 anos) com base no meu comportamento atual. "
        "Projete: (1) patrimônio acumulado em cada período, "
        "(2) impacto da inflação nas minhas despesas, "
        "(3) cenários otimista, realista e pessimista, "
        "(4) quanto preciso investir mensalmente para atingir independência financeira, "
        "(5) mudanças de comportamento que teriam maior impacto no longo prazo.",
    ),
}


def _fmt(value: float) -> str:
    return f"R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def prepare_financial_context(db, user_id: int) -> str:
    """Build a rich financial summary to send as context to the AI."""
    now = datetime.now()
    lines = ["=" * 55, "DADOS FINANCEIROS — FinanceControl", "=" * 55, ""]

    # ── Accounts ──────────────────────────────────────────────
    accounts = db.get_accounts(user_id)
    total = sum(a["balance"] for a in accounts)
    lines += [
        "💰 PATRIMÔNIO",
        f"  Saldo total: {_fmt(total)}",
    ]
    type_labels = {
        "checking": "Conta Corrente", "savings": "Poupança",
        "credit": "Cartão de Crédito", "cash": "Dinheiro",
        "investment": "Investimento",
    }
    for a in accounts:
        lines.append(f"  • {a['name']} ({type_labels.get(a['type'], a['type'])}): {_fmt(a['balance'])}")
    lines.append("")

    # ── Monthly history (last 12 months) ──────────────────────
    lines += ["📅 HISTÓRICO MENSAL (últimos 12 meses)",
              "  Mês              | Receitas      | Despesas      | Saldo"]
    monthly_incomes = []
    monthly_expenses = []

    for i in range(11, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year = now.year - ((now.month - i - 1) // 12)
        s = db.get_monthly_summary(user_id, month, year)
        label = f"{MONTH_NAMES[month-1][:3]}/{year}"
        monthly_incomes.append(s["income"])
        monthly_expenses.append(s["expense"])
        lines.append(
            f"  {label:<16}| {_fmt(s['income']):<13} | {_fmt(s['expense']):<13} | {_fmt(s['balance'])}"
        )

    avg_income = sum(monthly_incomes) / 12 if monthly_incomes else 0
    avg_expense = sum(monthly_expenses) / 12 if monthly_expenses else 0
    lines += [
        "",
        f"  Média mensal: Receitas {_fmt(avg_income)} | Despesas {_fmt(avg_expense)}",
        f"  Taxa de poupança média: {((avg_income - avg_expense) / avg_income * 100) if avg_income else 0:.1f}%",
        "",
    ]

    # ── Current month category breakdown ──────────────────────
    cats = db.get_expense_by_category(user_id, now.month, now.year)
    total_exp_month = sum(c["total"] for c in cats)
    if cats:
        lines += [f"🏷️ GASTOS POR CATEGORIA — {MONTH_NAMES[now.month-1]}/{now.year}"]
        for c in cats:
            pct = c["total"] / total_exp_month * 100 if total_exp_month else 0
            lines.append(f"  • {c['name']}: {_fmt(c['total'])} ({pct:.1f}%)")
        lines.append("")

    # ── Recent transactions (last 30) ─────────────────────────
    recent = db.get_transactions(user_id, limit=30)
    if recent:
        lines += ["💳 ÚLTIMAS 30 TRANSAÇÕES"]
        for t in recent:
            try:
                d = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                d = t["date"]
            tipo = "Receita" if t["type"] == "income" else "Despesa"
            cat = t.get("category_name") or "—"
            desc = t.get("description") or "—"
            lines.append(f"  {d} | {tipo} | {cat} | {desc} | {_fmt(t['amount'])}")
        lines.append("")

    # ── Budgets ────────────────────────────────────────────────
    budgets = db.get_budgets(user_id, now.month, now.year)
    if budgets:
        lines += [f"🎯 ORÇAMENTOS — {MONTH_NAMES[now.month-1]}/{now.year}"]
        for b in budgets:
            spent = b.get("spent") or 0
            pct = spent / b["amount"] * 100 if b["amount"] else 0
            status = "✅" if pct < 80 else "⚠️" if pct < 100 else "🔴"
            lines.append(
                f"  {status} {b.get('category_name','?')}: "
                f"gasto {_fmt(spent)} de {_fmt(b['amount'])} ({pct:.0f}%)"
            )
        lines.append("")

    lines.append("=" * 55)
    return "\n".join(lines)


class AIWorker(QThread):
    """Calls the Claude API with streaming and emits text chunks in real time."""
    chunk = pyqtSignal(str)
    done = pyqtSignal(int)       # emits total input+output tokens
    error = pyqtSignal(str)

    def __init__(self, api_key: str, model: str, system: str, prompt: str):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.system = system
        self.prompt = prompt
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            import anthropic
        except ImportError:
            self.error.emit(
                "Pacote 'anthropic' não instalado.\n\n"
                "Abra o terminal e execute:\n\n    pip install anthropic\n\nDepois reinicie o app."
            )
            return

        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            total_tokens = 0
            with client.messages.stream(
                model=self.model,
                max_tokens=3000,
                system=self.system,
                messages=[{"role": "user", "content": self.prompt}],
            ) as stream:
                for text in stream.text_stream:
                    if self._cancelled:
                        break
                    self.chunk.emit(text)
                usage = stream.get_final_message().usage
                total_tokens = usage.input_tokens + usage.output_tokens
            self.done.emit(total_tokens)
        except Exception as e:
            err = str(e)
            if "authentication" in err.lower() or "api_key" in err.lower():
                err = "Chave de API inválida. Verifique nas configurações."
            elif "model" in err.lower():
                err = f"Modelo não disponível: {self.model}"
            self.error.emit(err)
