# Garimpo de hardware

Monitor de resultados recentes para RTX 5060 Ti, placas-mãe LGA 1851 e memórias DDR5. A cada execução, consulta o RSS de busca do Google Notícias (janela de sete dias), identifica preços no formato brasileiro e envia pelo Telegram os links que ainda não foram notificados.

> O RSS do Google Notícias não é um comparador de preços nem garante que cada resultado seja uma oferta válida. O preço só aparece no alerta quando é encontrado no título ou resumo. Confira disponibilidade, frete e preço no site da loja.

## Executar localmente

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GARIMPO_DRY_RUN = "1"
python -m src.main
```

O modo de simulação imprime os resultados sem exigir dados do Telegram nem gravar o histórico. Para enviar alertas, configure as variáveis de ambiente `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` e execute `python -m src.main` sem `GARIMPO_DRY_RUN`. O histórico local fica em `.state/garimpo.sqlite3`.

### Criar o bot do Telegram

1. No Telegram, converse com `@BotFather`, envie `/newbot` e siga as instruções. Guarde o token fornecido em local seguro; ele permite controlar o bot.
2. Abra o bot que você criou e envie uma mensagem, por exemplo `/start`.
3. Defina o token no PowerShell e consulte as atualizações para obter o `chat.id` da conversa:

   ```powershell
   $token = Read-Host "Token do BotFather" -AsSecureString
   $env:TELEGRAM_BOT_TOKEN = (New-Object System.Net.NetworkCredential("", $token)).Password
   (Invoke-RestMethod "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/getUpdates").result.message.chat.id
   Remove-Item Env:\TELEGRAM_BOT_TOKEN
   ```

   O token é solicitado sem aparecer na tela e removido do ambiente ao final. Não publique nem compartilhe o token. Se o resultado vier vazio, envie outra mensagem ao bot e consulte novamente.

Edite [`config/items.json`](./config/items.json) para personalizar os itens e termos pesquisados.

## GitHub Actions

O workflow `.github/workflows/garimpo.yml` agenda execuções a cada cinco minutos, todos os dias, e também pode ser iniciado manualmente pela aba **Actions**. Para habilitá-lo:

1. Envie o projeto para o GitHub e deixe o workflow na branch padrão do repositório.
2. Em **Settings → Secrets and variables → Actions**, crie os secrets `TELEGRAM_BOT_TOKEN` (token do BotFather) e `TELEGRAM_CHAT_ID` (ID obtido na etapa acima).
3. Confirme que **Actions** está habilitado para o repositório.

O histórico de links já notificados é guardado no cache do Actions para reduzir alertas repetidos entre execuções. O cache é temporário; se ele expirar ou for removido, resultados antigos podem ser notificados novamente.

### Custo e confiabilidade

Para repositórios públicos, os runners padrão do GitHub Actions normalmente não consomem minutos pagos. Em repositórios privados, o uso depende da franquia e do plano; a cada cinco minutos podem ocorrer até 8.640 execuções por mês, portanto não há garantia de custo zero em uma conta privada. O Telegram é um serviço externo e suas condições podem mudar.

O GitHub pode atrasar ou descartar execuções agendadas em períodos de alta demanda. Portanto, o intervalo de cinco minutos é uma frequência solicitada, não uma garantia de execução pontual.
