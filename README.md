# Publicar a Activity no GitHub Pages

Este site hospeda os arquivos do EmulatorJS, seus 48 cores e o SDK do Discord
no GitHub Pages. Durante a publicação, ele baixa as ROMs da pasta `rom` do
repositório [pedecoca/EmulatorJS](https://github.com/pedecoca/EmulatorJS/tree/main/rom)
e as publica junto do site para aparecerem no seletor de jogos. O repositório
da Activity não recebe ROMs nem arquivos do bot.

A Activity oferece os sistemas e cores publicados pelo EmulatorJS 4.2.3. O
seletor de jogos mostra somente ROMs compatíveis que estejam no repositório
EmulatorJS. No momento, se a pasta `rom` tiver apenas arquivos `.gba`, somente
o Game Boy Advance terá jogos para iniciar.

Para adicionar jogos de outros sistemas, organize os arquivos em uma pasta
com o ID do core em `rom/`, por exemplo `rom/snes9x/jogo.sfc`,
`rom/mgba/jogo.gba` ou `rom/melonds/jogo.nds`. Os IDs e formatos reconhecidos
estão em [`systems.json`](./systems.json). Arquivos soltos diretamente em `rom/`
são associados automaticamente apenas quando sua extensão identifica um único
sistema; formatos ambíguos devem ficar na pasta do core correspondente. Depois,
execute novamente o workflow do GitHub Pages.

O Nintendo DS usa o core `melonds` por padrão e aparece no seletor mesmo antes
de haver ROMs `.nds`. Coloque as ROMs em `rom/melonds/`; o BIOS do DS não é
incluído pelo EmulatorJS e, se o jogo exigir, deve ser fornecido separadamente.
Os dois botões L/R, ABXY e Start/Select ficam nos controles de toque; a tela
inferior aceita toque/stylus no canvas quando o core permite ponteiro. As capas
de DS são procuradas no Libretro durante o deploy e salvas em
`asset/covers/`; a primeira publicação com uma ROM nova pode demorar um pouco
mais para baixar a capa.

No Nintendo DS, a Activity ativa o renderizador threaded do melonDS, desliga
o VSync e usa áudio de 10 bits sem interpolação por padrão. O botão
**DS: 1 tela** troca para o layout de tela superior e reduz o trabalho de
vídeo quando o jogo estiver lento; toque novamente para voltar às duas telas.
O core threaded só é usado quando o navegador expõe `SharedArrayBuffer`.

O console mostra os controles de toque abaixo da tela. Eles usam os botões
padrão do RetroPad, funcionam ao pressionar e segurar (inclusive em
combinações) e são habilitados quando o jogo inicia. O layout é recalculado
quando a Activity é redimensionada ou volta a ficar visível. No menu
**Controles**, o usuário pode escolher direcional ou bolinha analógica,
ajustar o tamanho dos controles de 70% a 140% com o slider ou os botões
**−**/**+** e usar **Mover controles** para arrastar o direcional e os botões
para outra posição. As preferências ficam salvas no dispositivo.

## Saves na nuvem dentro do Discord

A API de saves fica em `api.pokedc.online`. Como Activities são executadas
atrás do proxy `*.discordsays.com`, requisições absolutas para domínios
externos são bloqueadas pela CSP. No Developer Portal, em
**Activities → URL Mappings**, configure:

| Prefix | Target |
|---|---|
| `/api` | `api.pokedc.online` |

Com esse mapping, a Activity usa `/api/emu/...` e o Discord encaminha para a
API. O servidor também aceita o caminho `/emu/...` para o caso de o proxy
remover o prefixo `/api`.

Dentro do Discord, o catálogo também tenta `/api/roms.json`, `/api/systems.json`
e `/api/covers.json` antes de usar os arquivos estáticos do GitHub Pages.

As ROMs de Nintendo DS são servidas pelo GitHub Release `nds-roms-v1`
(manifesto `nds_release.json`); a API faz o proxy com suporte a `Range` para
o Discord não precisar carregar os arquivos do repositório de ROMs. Isso
permite jogar ROMs grandes que estão apenas no servidor local, sem publicá-las
no repositório do Pages; se a API estiver fora, a Activity usa o catálogo
estático como reserva.

Para os saves aparecerem no PC e no celular, abra a Activity **pelo Discord**
nos dois aparelhos e entre com a mesma conta.

A identidade do save usa o token OAuth quando ele existe. Antes de abrir o
popup de autorização, a Activity tenta `authenticate({})` e o
`getActivityInstanceConnectedParticipants()` com algumas tentativas, porque a
lista de participantes pode demorar a ser preenchida pelo cliente Discord.
Se o ID vier da Activity, ele é usado diretamente pelo header
`X-Discord-User-ID`, sem exigir popup de autorização. A prévia em
`http://127.0.0.1:8081` ou em um navegador comum, fora do Discord, usa somente
o IndexedDB local porque não há OAuth do Discord nesse modo.

## Publicar

1. Crie um repositório **público** no GitHub para a Activity.
2. No terminal, entre nesta pasta (`activity-pages`) e envie somente o conteúdo
   dela para a branch `main`, incluindo a pasta oculta `.github`.
3. No repositório, abra **Settings → Secrets and variables → Actions → Variables**
   e crie `DISCORD_CLIENT_ID` com o Application ID do aplicativo Discord.
   Esse ID é público; não coloque o token do bot aqui.
4. Em **Settings → Pages**, selecione **GitHub Actions** como origem.
5. Abra a aba **Actions** e espere o fluxo **Deploy Discord Activity to GitHub
   Pages** terminar. O endereço publicado aparece no resultado do deploy.
6. Configure esse endereço como URL da Activity no Developer Portal do Discord.

Para criar e enviar o repositório usando Git, execute os comandos dentro desta
pasta, substituindo `USUARIO/REPOSITORIO` pelo repositório recém-criado:

```powershell
git init
git add index.html README.md systems.json .github/workflows/pages.yml
git commit -m "Publish Discord Activity on GitHub Pages"
git branch -M main
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

O workflow fixa EmulatorJS e os 48 cores na versão `4.2.3` e o SDK do Discord
na `2.5.0`. Ele usa o Application ID configurado nas variáveis do repositório
e atualiza o catálogo de jogos a partir da pasta `rom` do repositório
EmulatorJS em cada publicação. As ROMs copiadas e os arquivos do site ficam
disponíveis publicamente no GitHub Pages.
# Publicar a Activity no GitHub Pages

Este site hospeda os arquivos do EmulatorJS, o core mGBA e o SDK do Discord no
GitHub Pages. O fluxo baixa somente os arquivos necessários; não inclui ROMs
nem arquivos do bot no repositório da Activity. Durante a publicação, ele
obtém os arquivos `.gba` da pasta `rom` do repositório
[pedecoca/EmulatorJS](https://github.com/pedecoca/EmulatorJS/tree/main/rom) e
os publica junto do site para aparecerem no seletor de jogos.

## Publicar

1. Crie um repositório **público** no GitHub para a Activity.
2. No terminal, entre nesta pasta (`activity-pages`) e envie somente o conteúdo
   dela para a branch `main`, incluindo a pasta oculta `.github`.
3. No repositório, abra **Settings → Secrets and variables → Actions → Variables**
   e crie `DISCORD_CLIENT_ID` com o Application ID do aplicativo Discord.
   Esse ID é público; não coloque o token do bot aqui.
4. Em **Settings → Pages**, selecione **GitHub Actions** como origem.
5. Abra a aba **Actions** e espere o fluxo **Deploy Discord Activity to GitHub
   Pages** terminar. O endereço publicado aparece no resultado do deploy.
6. Configure esse endereço como URL da Activity no Developer Portal do Discord.

Para criar e enviar o repositório usando Git, execute os comandos dentro desta
pasta, substituindo `USUARIO/REPOSITORIO` pelo repositório recém-criado:

```powershell
git init
git add index.html README.md .github/workflows/pages.yml
git commit -m "Publish Discord Activity on GitHub Pages"
git branch -M main
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

O workflow fixa EmulatorJS e o core mGBA na versão `4.2.3` e o SDK do Discord
na `2.5.0`. Ele inclui as licenças GPL-3.0 e MIT no site publicado, usa o
Application ID configurado nas variáveis do repositório e atualiza o catálogo
de jogos a partir da pasta `rom` do repositório EmulatorJS em cada publicação.
Os arquivos `.gba` copiados ficam disponíveis publicamente no GitHub Pages.
