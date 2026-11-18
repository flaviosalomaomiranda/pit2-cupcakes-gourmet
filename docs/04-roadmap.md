# Roadmap (evolução após o PIT II)

| Fase | Item | Por quê | Esforço |
|---|---|---|---|
| v1.1 | Ajustes vindos dos 5 avaliadores | Ciclo Kaizen | P |
| v1.2 | Gateway real (Mercado Pago/PagSeguro) com webhook assinado | Sair do pagamento simulado; a troca fica só em `services/pagamento.py` | M |
| v1.2 | PostgreSQL gerenciado (Render/Supabase) | Persistência em produção e concorrência de escrita | P (SQL já é padrão) |
| v1.3 | Cadastro e login de cliente, endereços salvos e histórico | Recompra mais rápida | M |
| v1.3 | CRUD de cupcakes e de zonas de frete no painel, com fotos reais | Autonomia do lojista | M |
| v1.4 | Notificação de status por WhatsApp/e-mail | US09 sem precisar abrir a página | M |
| v1.4 | PWA (instalar na tela inicial, ícone, offline da vitrine) | Experiência de app sem loja de apps | P |
| v2.0 | Cupons, programa de fidelidade, relatórios de vendas | Crescimento do negócio | G |
| ✅ Feito | CI no GitHub Actions (`.github/workflows/testes.yml`) roda os testes a cada push | Evitar regressões | P |
