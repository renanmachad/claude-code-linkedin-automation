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

## Instalação

### Como plugin (recomendado)

Este repositório também é um marketplace de plugins do Claude Code. No terminal:

```bash
claude plugin marketplace add renanmachad/claude-code-linkedin-automation
```

```bash
claude plugin install linkedin-job-outreach@renanmachad-plugins
```

Ou, dentro de uma sessão do Claude Code: `/plugin marketplace add renanmachad/claude-code-linkedin-automation` e depois `/plugin install linkedin-job-outreach@renanmachad-plugins`.

Para receber atualizações: `claude plugin marketplace update renanmachad-plugins`. Para remover: `claude plugin marketplace remove renanmachad-plugins`.

> Instalado como plugin, os arquivos ficam em `~/.claude/plugins/cache/` e são substituídos a cada atualização. Para personalizar o `references/profile.md` (próxima seção) sem perder a edição, prefira a instalação manual abaixo.

### Manual (clonando a pasta)

A skill também funciona clonada direto em uma pasta de skills do Claude Code:

**Para todos os seus projetos** (pasta pessoal):

```bash
git clone https://github.com/renanmachad/claude-code-linkedin-automation.git ~/.claude/skills/linkedin-job-outreach
```

No Windows (PowerShell), o caminho equivalente é `$env:USERPROFILE\.claude\skills\linkedin-job-outreach`.

**Só em um projeto** (versionada junto com ele):

```bash
git clone https://github.com/renanmachad/claude-code-linkedin-automation.git .claude/skills/linkedin-job-outreach
```

Abra uma nova sessão do Claude Code (skills são carregadas no início da sessão) e peça `busca vagas` para testar. Para atualizar depois: `git pull` dentro da pasta da skill.

## Personalize antes de usar

A skill vem com o perfil do autor. **Edite `references/profile.md`** com os seus dados — é dele que saem a nota de fit e o conteúdo das mensagens:

- **Quem é / Stack**: experiência, empresas, tecnologias. A skill não cita na mensagem nada que não esteja aqui.
- **Condições**: regime (PJ/CLT/contractor) e modelo (remoto/híbrido). O que for eliminatório zera a nota.
- **Pontuação**: pesos de cada critério.
- **Ângulos de pitch**: qual destaque usar para cada tipo de vaga.

Também vale revisar:

- `references/messages.md` — tom, tamanho e exemplos de mensagem.
- `references/red-flags.md` — padrões de golpe que descartam a vaga.
- Termos de busca padrão e limite diário em `SKILL.md` (seção "Busca autônoma no Chrome" e "Regras inegociáveis").

## Como usar

Com o Chrome aberto e o LinkedIn logado, peça em linguagem natural:

| Pedido | O que acontece |
|---|---|
| `busca vagas` | Busca com os termos padrão, priorizando posts de conexões de 1º grau, e devolve a lista para aprovação |
| `busca vagas de "senior react remote"` | Mesma coisa com os termos que você passar |
| `analisa esta vaga: <url ou texto do post>` | Triagem e mensagem para um post específico |
| `processa meus alertas de vaga do Gmail` | Lê os alertas dos últimos 3 dias e faz a triagem |
| `manda 1, 3 e 4` | Envia só as mensagens aprovadas e registra no tracker |
| `quem não respondeu?` | Lista contatos sem resposta há 7+ dias e sugere follow-up |
| `a Fulana respondeu` / `tenho entrevista com a Empresa X` | Atualiza o status no tracker |

### Tracker (também dá para usar direto)

O banco fica em `~/.linkedin-job-outreach/tracker.db` (criado na primeira execução; mude com a variável `JOB_OUTREACH_DB`).

```bash
python scripts/tracker.py check --name "Fulana" --company "Empresa"   # já contatei?
python scripts/tracker.py today                                       # quantos envios hoje (limite 10)
python scripts/tracker.py list --status sent --older-than 7           # sem resposta há 7+ dias
python scripts/tracker.py update --id 3 --status interview            # replied|interview|rejected|ghosted
python scripts/tracker.py stats                                       # funil
```

## Segurança e limites

- **Nada é enviado sem sua aprovação**, mensagem por mensagem, no chat. Antes de digitar, a skill lê o histórico da conversa e não duplica contato feito à mão.
- **Risco de conta**: os termos do LinkedIn proíbem automação. A skill usa o seu navegador real, em ritmo lento, com teto de 10 abordagens/dia, e para imediatamente diante de CAPTCHA, aviso de atividade incomum ou tela de login. Isso reduz o risco, mas não elimina — use por sua conta.
- **DM só para conexões de 1º grau** (sem Premium). Para os demais, o caminho é convite com nota de até 200 caracteres, e contas gratuitas têm um número limitado de notas por mês; quando acabam, a skill fecha o modal sem enviar e sugere alternativas.
- Posts que pedem para clonar repositório/rodar código antes de uma conversa real, cobram taxa ou pedem documentos são descartados como golpe (ver `references/red-flags.md`).

## Estrutura

```
SKILL.md                 # fluxo e regras que o Claude segue
references/profile.md    # seu perfil e critérios de nota (edite!)
references/messages.md   # regras e exemplos de mensagem
references/red-flags.md  # padrões de golpe
scripts/tracker.py       # CLI do tracker (SQLite, sem dependências)
```
