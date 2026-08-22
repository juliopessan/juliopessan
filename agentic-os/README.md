# Órbita OS

Painel de comando para um workspace agêntico rodando em cima do Claude Code.
Arquivo único, sem build, sem dependência: abra `index.html` no navegador.

![Órbita OS](preview.png)

## O que é

Uma releitura do padrão de "Agentic OS" popularizado pelo Rubric (Jay E / RoboNuggets),
organizada em torno do framework **ARMS** — os quatro elementos que sustentam um
workspace agêntico:

| | Camada | No painel |
|---|---|---|
| **A** | Aplicações | Trilho de micro apps, conectores |
| **R** | Rotinas | Tabela de tarefas agendadas com a próxima destacada |
| **M** | Memória | Núcleo do Segundo Cérebro — o mapa dos arquivos roteadores |
| **S** | Skills | Deck de skills com modelo e esforço por execução |

Mais o **anel de artefatos**: um índice visual e buscável de tudo que o agente já
produziu, porque achar de novo o que foi gerado há três semanas é o gargalo real.

## Dados ao vivo

Publicado como Artifact no claude.ai, o painel declara a capability `mcp` e lê os
conectores **com as credenciais de quem está vendo a página** — nenhum token passa
pelo código, nada é assado no arquivo:

| Painel | Conector | Ferramenta |
|---|---|---|
| Agenda | Google Calendar | `list_events` (janela do dia, refaz a cada 5 min) |
| Caixa de entrada | Gmail | `search_threads` — uma leitura de volume, outra do que pede atenção |
| Anel de artefatos | Google Drive | `list_recent_files` (26 peças, por recência) |

Cada nó do anel abre o arquivo real no Drive. A mistura da caixa de entrada é
calculada por domínio de remetente: quem mais te escreveu nas últimas 24 h.

**Fora do claude.ai** — abrindo `index.html` direto do disco — não existe
`window.claude`, então o painel cai no conteúdo de exemplo do objeto `OS` e diz
isso no rodapé de cada seção. Nenhum número fictício jamais aparece sem o selo
`números de exemplo`.

**Falhas são tratadas uma a uma**, nunca num aviso genérico: conector ausente
("Adicione o Gmail"), credencial expirada ("Reconecte"), bloqueio por política,
upstream fora do ar (mantém o último resultado bom e marca como defasado). Uma
seção que falha não derruba as outras.

**Privacidade:** uma página que declara `mcp` não pode ser compartilhada
publicamente — é a regra da plataforma, e ela existe justamente porque a página
alcança dados conectados.

## O que ainda é estático

- **Rotinas** — snapshot real das suas Routines. Não há conector de Routines no
  claude.ai, então a lista não se atualiza sozinha; o rodapé do painel avisa.
- **Deck de skills** — suas skills reais, com modelo e esforço por execução.
- **Segundo Cérebro** — mapa dos departamentos que roteiam as skills.
- **Micro apps** — atalhos para Artifacts, Drive e seus repositórios.

Tudo vem do objeto `OS`, no topo do `<script>`:

```js
const OS = {
  timezone: 'America/Sao_Paulo',
  microApps: [...], skills: [...], routines: [...], brain: {...},
  agenda: [...], email: {...}, artifacts: [...]   // usados só como fallback
};
```

## Disparo headless de skills

Cada card do deck monta o comando com o modelo e o esforço escolhidos e copia para
a área de transferência — o botão diz `Comando` porque é exatamente isso que ele faz.
Uma página estática não abre processo:

```bash
MAX_THINKING_TOKENS=31999 claude -p "/newsletter-maestro" --model claude-opus-5
```

Para o botão executar de verdade, sirva a página por um processo mínimo que exponha
`POST /run` fazendo spawn desse comando e devolvendo a saída. O painel não muda:
só o handler de `data-run`.

## Detalhes de implementação

- **Anel** — nós posicionados por `transform: rotate(θ) translate(R) rotate(-θ)`,
  com contra-rotação no botão para o ícone ficar sempre em pé. A órbita pausa ao
  apontar, ao buscar e ao filtrar por tipo.
- **Núcleo** — nuvem de 300 pontos em esfera de Fibonacci, arestas pré-calculadas
  por vizinho mais próximo, projeção em canvas 2D. Um frame estático sob
  `prefers-reduced-motion`.
- **Relógio** — `Intl.DateTimeFormat` com `timeZone`, sem biblioteca de datas.
  Agenda e rotinas recalculam estado a cada 30 s a partir da hora local do fuso.
- **Tema** — escuro por decisão, não por omissão: é um console. Todas as cores
  saem de tokens em `:root` e o `body` pinta o próprio fundo.
- **Dados de terceiros** — todo texto vindo de conector passa por `esc()` antes de
  entrar no DOM. Assunto de e-mail e nome de arquivo são conteúdo não confiável.
- **Atalhos** — `/` foca a busca, `Esc` fecha o painel de detalhe.

## Créditos

Framework ARMS e o formato de dashboard: Jay E (RoboNuggets), no vídeo
"O NOVO padrão de SO Agêntico para modelos Claude 5". Implementação e design daqui
são originais.
