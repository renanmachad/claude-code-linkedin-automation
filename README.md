# LinkedIn Job Outreach — skill para Claude Code

Skill que busca posts de vaga no LinkedIn pelo seu próprio Chrome, faz a triagem (red flags, nota de fit 0–10), escreve a mensagem para o recrutador e **só envia as que você aprovar**, registrando cada contato em um banco SQLite local para evitar duplicatas e lembrar de follow-ups.

```
você: busca vagas
Claude: [busca no LinkedIn → lê posts → checa histórico → dá nota → escreve mensagens]
        ### [1] 9/10 — Full Stack Sênior @ Empresa X
        Recrutador: Fulana (1º grau) · Canal: DM
        Mensagem (341 caracteres): Oi, Fulana! Vi seu post...
        Quais envio?
você: manda 1 e 3
Claude: [envia, confere na tela, registra no tracker]
```

## Requisitos

- [Claude Code](https://claude.com/claude-code) (CLI, app desktop ou extensão de IDE)
- Python 3.8+ no `PATH` (só biblioteca padrão; nada para instalar via pip)
- Extensão [Claude in Chrome](https://chromewebstore.google.com/detail/fcoeoabgfenejglbffodgkkbkcdhcgfn), logada na mesma conta do Claude Code
- LinkedIn logado nesse Chrome
- Opcional: conector do Gmail, para processar alertas de vaga (`jobalerts-noreply@linkedin.com`)

> **Windows:** instale o Python com `winget install -e --id Python.Python.3.12 --scope user` e desligue os aliases "python.exe"/"python3.exe" em *Configurações → Aplicativos → Configurações avançadas → Aliases de execução de aplicativo*; senão `python` abre a Microsoft Store.

## Instalação rápida

### Opção 1 — colar um prompt no Claude Code

Abra o Claude Code (terminal, app desktop ou IDE) e cole:

```text
Instale o plugin linkedin-job-outreach para mim:
1. Rode `claude plugin marketplace add renanmachad/claude-code-linkedin-automation`.
2. Rode `claude plugin install linkedin-job-outreach@renanmachad-plugins`.
3. Confirme com `claude plugin details linkedin-job-outreach` que aparece "Skills (1) linkedin-job-outreach".
4. Verifique se `python --version` retorna Python 3.8 ou superior; se não, me diga como instalar no meu sistema.
Se o comando `claude` não estiver no PATH, pare e me diga para digitar eu mesmo
`/plugin marketplace add renanmachad/claude-code-linkedin-automation` e
`/plugin install linkedin-job-outreach@renanmachad-plugins`.
No fim, me lembre de rodar /reload-plugins ou abrir uma nova sessão.
```

### Opção 2 — comandos no terminal

```bash
claude plugin marketplace add renanmachad/claude-code-linkedin-automation
```

```bash
claude plugin install linkedin-job-outreach@renanmachad-plugins
```

Ou, dentro de uma sessão do Claude Code:

```text
/plugin marketplace add renanmachad/claude-code-linkedin-automation
/plugin install linkedin-job-outreach@renanmachad-plugins
```

Depois de instalar, rode `/reload-plugins` ou abra uma nova sessão.

### Atualizar e remover

```bash
claude plugin marketplace update renanmachad-plugins
```

```bash
claude plugin marketplace remove renanmachad-plugins
```

Seu perfil, seu CV e o histórico de contatos ficam em `~/.linkedin-job-outreach/`, fora da pasta do plugin: atualizar ou remover o plugin não apaga nada disso.

### Alternativa — clonar como skill avulsa

Útil para quem quer editar a skill em si (regras, mensagens, red flags). Nesse modo os comandos `/linkedin-job-outreach:follow-up` e `/linkedin-job-outreach:cv` não aparecem, mas pedir "faz follow-up das minhas DMs" ou "lê meu CV em <caminho>" funciona do mesmo jeito.

```bash
git clone https://github.com/renanmachad/claude-code-linkedin-automation.git ~/.claude/skills/linkedin-job-outreach
```

No Windows (PowerShell):

```powershell
git clone https://github.com/renanmachad/claude-code-linkedin-automation.git "$env:USERPROFILE\.claude\skills\linkedin-job-outreach"
```

Para atualizar: `git pull` dentro da pasta da skill.

## Configure seu perfil

A skill não vem com perfil: a nota de fit, os termos de busca, o limite diário e o conteúdo das mensagens saem de `~/.linkedin-job-outreach/profile.md`, criado na primeira vez a partir de [`references/profile.template.md`](references/profile.template.md). Com o Chrome aberto e o LinkedIn logado, cole no Claude Code:

```text
Configure meu perfil da skill linkedin-job-outreach. Leia meu perfil do LinkedIn
no Chrome (só leitura) e me pergunte o que faltar: regime de contratação que aceito,
modelo de trabalho, localização, prioridades, idiomas, termos de busca e limite diário.
Me mostre o perfil completo antes de salvar.
```

Prefere não deixar o Claude ler seu LinkedIn? Troque a segunda frase por "Me faça as perguntas no chat". Para ajustar depois, edite o arquivo direto ou peça "atualiza meu perfil de busca: agora aceito híbrido em São Paulo".

### Importe seu CV (opcional, recomendado)

Com o CV, as mensagens citam experiências e resultados concretos em vez de só a lista de tecnologias. Cole no Claude Code, trocando o caminho:

```text
/linkedin-job-outreach:cv C:\Users\voce\Documents\curriculo.pdf
```

Aceita PDF, DOCX, MD e TXT. O arquivo é copiado para `~/.linkedin-job-outreach/cv/` e lido; os fatos vão para `~/.linkedin-job-outreach/cv/memoria.md`, que a busca, as abordagens e o follow-up passam a usar. Mudou o currículo? Rode o comando de novo com o novo caminho, ou sem caminho para reler o mesmo arquivo — a memória é reescrita a cada execução e o Claude mostra o que mudou e sugere ajustes no perfil.

O que cada seção do perfil controla:

- **Quem é / Stack**: experiência e tecnologias. A skill não cita na mensagem nada que não esteja aqui.
- **Condições**: regime, modelo, localização. O que for eliminatório zera a nota.
- **Busca**: termos padrão e limite diário de abordagens.
- **Pontuação** e **Ângulos de pitch**: pesos da nota e o destaque para cada tipo de vaga.

## Como usar

Com o Chrome aberto e o LinkedIn logado, peça em linguagem natural:

| Pedido | O que acontece |
|---|---|
| `/linkedin-job-outreach:cv <caminho>` ou `lê meu CV` | Importa/relê o CV e atualiza a memória usada nas mensagens |
| `configura meu perfil` | Configuração guiada do perfil (também roda sozinha no primeiro uso) |
| `busca vagas` | Busca com os termos do seu perfil, priorizando posts de conexões de 1º grau, e devolve a lista para aprovação |
| `busca vagas de "senior react remote"` | Mesma coisa com os termos que você passar |
| `analisa esta vaga: <url ou texto do post>` | Triagem e mensagem para um post específico |
| `processa meus alertas de vaga do Gmail` | Lê os alertas dos últimos 3 dias e faz a triagem |
| `manda 1, 3 e 4` | Envia só as mensagens aprovadas e registra no tracker |
| `/linkedin-job-outreach:follow-up` ou `faz follow-up das minhas DMs` | Percorre suas DMs, separa as conversas sobre vaga, identifica as paradas há 7+ dias e escreve um follow-up no idioma e tom de cada conversa; também aponta quem está esperando resposta sua. Aceita outro prazo: `/linkedin-job-outreach:follow-up 10` |
| `a Fulana respondeu` / `tenho entrevista com a Empresa X` | Atualiza o status no tracker |

### Tracker (também dá para usar direto)

O banco fica em `~/.linkedin-job-outreach/tracker.db` (criado na primeira execução; mude com a variável `JOB_OUTREACH_DB`). Os comandos abaixo são para a instalação por `git clone`, rodando dentro da pasta da skill.

```bash
python scripts/tracker.py check --name "Fulana" --company "Empresa"   # já contatei?
python scripts/tracker.py today                                       # quantos envios hoje (limite 10)
python scripts/tracker.py list --status sent --older-than 7           # sem resposta há 7+ dias
python scripts/tracker.py update --id 3 --status interview            # replied|interview|rejected|ghosted
python scripts/tracker.py stats                                       # funil
python scripts/tracker.py profile                                     # caminho e status do seu perfil
python scripts/tracker.py cv --import curriculo.pdf                   # copia o CV (sem --import: mostra o CV atual)
```

## Segurança e limites

- **Nada é enviado sem sua aprovação**, mensagem por mensagem, no chat. Antes de digitar, a skill lê o histórico da conversa e não duplica contato feito à mão.
- **Risco de conta**: os termos do LinkedIn proíbem automação. A skill usa o seu navegador real, em ritmo lento, com teto diário de abordagens (padrão 10), e para imediatamente diante de CAPTCHA, aviso de atividade incomum ou tela de login. Isso reduz o risco, mas não elimina — use por sua conta.
- **DM só para conexões de 1º grau** (sem Premium). Para os demais, o caminho é convite com nota de até 200 caracteres, e contas gratuitas têm um número limitado de notas por mês; quando acabam, a skill fecha o modal sem enviar e sugere alternativas.
- Posts que pedem para clonar repositório/rodar código antes de uma conversa real, cobram taxa ou pedem documentos são descartados como golpe (ver `references/red-flags.md`).

## Estrutura

```
SKILL.md                          # fluxo e regras que o Claude segue
skills/follow-up/SKILL.md         # comando de follow-up das DMs
skills/cv/SKILL.md                # comando de importar/ler o CV e gerar a memória
references/profile.template.md    # modelo do perfil (o seu fica em ~/.linkedin-job-outreach/)
references/messages.md            # regras e exemplos de mensagem
references/red-flags.md           # padrões de golpe
scripts/tracker.py                # CLI do tracker e do perfil (SQLite, sem dependências)
.claude-plugin/                   # manifestos do plugin e do marketplace
```

## Licença

[MIT](LICENSE)
