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
