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
com o ID do core em `rom/`, por exemplo `rom/snes9x/jogo.sfc` ou
`rom/pcsx_rearmed/jogo.chd`. Os IDs e formatos reconhecidos estão em
[`systems.json`](./systems.json). Arquivos soltos diretamente em `rom/` são
associados automaticamente apenas quando sua extensão identifica um único
sistema; formatos ambíguos devem ficar na pasta do core correspondente. Depois,
execute novamente o workflow do GitHub Pages.

O console mostra os controles de toque abaixo da tela. Eles usam os botões
padrão do RetroPad, funcionam ao pressionar e segurar (inclusive em
combinações) e são habilitados quando o jogo inicia. O layout é recalculado
quando a Activity é redimensionada ou volta a ficar visível.

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
