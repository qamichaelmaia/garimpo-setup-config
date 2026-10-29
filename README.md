# Garimpo de hardware

Monitor de ofertas recentes para placas de vídeo RTX 5060, RTX 5060 Ti de 8 GB ou 16 GB e RX 9060 XT de 16 GB, placas-mãe LGA 1851 DDR5, fontes de 650 W a 800 W, gabinetes e fans/ventoinhas de PC. A cada execução, busca promoções no Promobit e no Bilômetro e envia pelo Telegram apenas ofertas compatíveis, com preço atual, loja e link. Quando a fonte informa o preço anterior, ele também aparece no alerta. As placas de vídeo recebem a indicação **MEGA DESCONTO** quando o preço atual fica abaixo destes limites: RTX 5060 Ti 16 GB por R$ 3.300, RTX 5060 Ti 8 GB por R$ 2.700 e RX 9060 XT 16 GB por R$ 2.700. A indicação é enviada uma vez por anúncio quando ele fica abaixo do limite, mesmo que o link já tenha sido notificado antes. As RTX 5060 Ti e RX 9060 XT são priorizadas nos alertas, começando pelas ofertas publicadas no dia da execução. Quando disponíveis, também inclui imagem e cupom.

> Disponibilidade, frete, cupons e preços podem mudar. Ofertas do Promobit abrem a publicação para conferir os detalhes; as do Bilômetro usam o link de compra compartilhado por essa fonte.
>
> Essas fontes agregam anúncios de varejistas como Mercado Livre, KaBuM!, Pichau, TerabyteShop, Magalu e Shopee quando publicados. O monitor não consulta diretamente as APIs privadas de cada loja, então a cobertura depende das ofertas encontradas nos agregadores.

## Executar localmente

Requer Python 3.10 ou superior. O projeto usa apenas a biblioteca padrão do Python, sem dependências adicionais.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
$env:GARIMPO_DRY_RUN = "1"
python -m src.main
```

O modo de simulação imprime as ofertas sem exigir dados do Telegram nem gravar o histórico. Para enviar alertas, configure as variáveis de ambiente `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` e execute `python -m src.main` sem `GARIMPO_DRY_RUN`. O histórico local fica em `.state/garimpo.sqlite3`.

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

Edite [`config/items.json`](./config/items.json) para personalizar itens, buscas e palavras que devem ser excluídas. Um item pode usar uma busca (`query`) ou várias (`queries`). O monitor procura ofertas publicadas por ambas as fontes e ignora resultados sem preço ou link de compra/publicação.

## Fonte de ofertas

A coleta usa endpoints públicos consumidos pelos sites do Promobit e do Bilômetro. Eles não têm contrato público de estabilidade e podem mudar ou limitar consultas; se isso acontecer, a execução falhará visivelmente no log do GitHub Actions. São feitas buscas adicionais para a RTX 5060 Ti e a RX 9060 XT, mas as fontes podem limitar ou não retornar todos os anúncios; por isso, nenhuma automação consegue garantir que toda promoção será capturada. O Pelando retornou HTTP 403 ao GitHub Actions, e o Zoom/Buscapé não foi integrado por não termos identificado uma API pública documentada apropriada para este fluxo.

## GitHub Actions

O workflow `.github/workflows/garimpo.yml` agenda execuções a cada 20 minutos, todos os dias, e também pode ser iniciado manualmente pela aba **Actions**. Para habilitá-lo:

1. Envie o projeto para o GitHub e deixe o workflow na branch padrão do repositório.
2. Em **Settings → Secrets and variables → Actions**, crie os secrets `TELEGRAM_BOT_TOKEN` (token do BotFather) e `TELEGRAM_CHAT_ID` (ID obtido na etapa acima).
3. Confirme que **Actions** está habilitado para o repositório. Como o projeto não tem dependências externas, não há instalação de pacotes no workflow.

O histórico de links já notificados é guardado no cache do Actions para reduzir alertas repetidos entre execuções. O cache é temporário; se ele expirar ou for removido, resultados antigos podem ser notificados novamente.

### Custo e confiabilidade

Para repositórios públicos, os runners padrão do GitHub Actions normalmente não consomem minutos pagos. Em repositórios privados, o uso depende da franquia e do plano; a cada 20 minutos podem ocorrer cerca de 2.160 execuções em um mês de 30 dias, portanto não há garantia de custo zero em uma conta privada. O workflow consulta as duas fontes em cada execução. O Telegram é um serviço externo e suas condições podem mudar.

O GitHub pode atrasar ou descartar execuções agendadas em períodos de alta demanda. Portanto, o intervalo de 20 minutos é uma frequência solicitada, não uma garantia de execução pontual.
