# Manual de uso

## 1. Instalação

### Windows (mais fácil)
1. Instale o Python 3.10 ou mais novo em <https://www.python.org/downloads/>, marcando **"Add python.exe to PATH"**.
2. Dê dois cliques em **`INICIAR.bat`**. Na primeira vez ele cria o ambiente e instala as dependências (cerca de 1 minuto).
3. O navegador abre em `http://127.0.0.1:5000`. Deixe a janela preta aberta enquanto usa o sistema.

### Linux/macOS ou linha de comando
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # abre em http://127.0.0.1:5000
```

### Variáveis de ambiente (opcionais)

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada execução | Defina em produção para as sessões sobreviverem a reinícios |
| `ADMIN_USUARIO` / `ADMIN_SENHA` | `admin` / `cupcake123` | Credenciais do painel, aplicadas na criação do banco |
| `CUPCAKES_DB` | `instance/cupcakes.db` | Caminho do arquivo do banco |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Use `HOST=0.0.0.0` para acessar pelo celular na mesma rede |

Para zerar o banco: apague `instance/cupcakes.db` ou rode `flask --app run init-db`.

### Rodar os testes
```bash
python -m pytest tests -v                      # 100 testes unitários e de integração
node --test tests_front/utils.test.js          # 9 testes do JavaScript
pip install playwright && python -m playwright install chromium
python -m pytest tests_e2e -v                  # 2 testes de sistema no navegador (geram as capturas)
```

## 2. Uso pelo cliente

1. **Vitrine:** role os cupcakes, use as pílulas (Tradicionais, Diet, Salgados, Regionais) ou busque por nome ou ingrediente.
2. **Detalhe:** toque na foto para ver a descrição, os ingredientes e os alergênicos. Escolha a quantidade com + e −.
3. **Adicionar:** "+ Adicionar" põe 1 unidade no carrinho; o número no ícone do carrinho aumenta.
4. **Carrinho:** ajuste as quantidades (− até zero remove), marque a **embalagem presente** e escreva a mensagem do cartão (opcional).
5. **CEP:** digite o CEP e toque em "Calcular". Faixas atendidas na demonstração: 76800-001 a 76834-999 (Porto Velho).
6. **Pagamento:** preencha nome, celular, e-mail e endereço e escolha:
   - **PIX:** aparece o QR Code e o "Copia e Cola", válidos por 15 minutos. No ambiente acadêmico, toque em **"Simular confirmação do banco"**.
   - **Cartão:** use `4111 1111 1111 1111` (aprovado) ou `4000 0000 0000 0002` (recusado), com validade futura e qualquer CVV de 3 dígitos.
7. **Acompanhar:** a linha do tempo mostra Recebido → Em preparo → Saiu para entrega → Entregue, com horários. Guarde o **código de 8 letras**: em "Meus pedidos" dá para consultar de outro aparelho.

## 3. Uso pelo lojista

1. Acesse **`/admin`** e entre com `admin` / `cupcake123`.
2. Clique em **"🔔 Ativar alerta sonoro"**: o navegador exige um clique antes de tocar sons. O painel verifica novos pedidos a cada 15 s, toca um bip e mostra o aviso "Novo pedido pago!".
3. Cada cartão de pedido mostra o cliente, o telefone, o endereço, os itens e, em destaque, **PRESENTE** com a mensagem do cartão.
4. Use o botão principal para avançar: **Em preparo → Saiu para entrega → Entregue**. "Cancelar" pede confirmação.
5. Filtre pelas pílulas de status. "Em andamento" mostra o que precisa de ação.
6. Para sair, use "Sair".

## 4. Problemas comuns

| Problema | Solução |
|---|---|
| "Python não encontrado" | Reinstale o Python marcando "Add python.exe to PATH" |
| "Sessão expirada ou formulário inválido" | A página ficou aberta antes de o servidor reiniciar. Recarregue (F5). |
| O alerta do painel não toca | Clique em "Ativar alerta sonoro" uma vez |
| O celular não abre o endereço | Confira se está na mesma Wi-Fi e use `http://IP-DO-PC:5000`; libere o Python no Firewall do Windows |
