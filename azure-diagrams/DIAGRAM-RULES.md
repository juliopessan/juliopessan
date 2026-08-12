# Regras — Diagramas Azure em draw.io (padrão Microsoft Architecture Center)

Regras obrigatórias para TODA geração de diagramas `.drawio` a partir de Mermaid ou descrição de arquitetura. Modelo de referência: `reference.svg` (Microsoft Architecture Center).

> Inspirado por ideias do projeto [archify](https://github.com/tt-a1i/archify) (jul/2026): taxonomia de códigos de regra para diagnósticos estruturados (§0.2) e seleção explícita de modo antes de desenhar (§0.3). Estrutura, pipeline e estilo visual existentes permanecem inalterados.

## 0.1a Pacotes de ícones oficiais offline

Além da validação online via `search_shapes` / HTTP HEAD contra `app.diagrams.net/img/lib/azure2/...` (seção 5), o repositório mantém uma cópia local dos pacotes oficiais de ícones da Microsoft em `assets/icon-packs/`, para os casos em que o serviço de ícones não tem um SVG azure2 equivalente (M365, Power Platform) ou quando é preciso trabalhar offline:

| Arquivo | Conteúdo | Uso |
|---|---|---|
| `Azure_Public_Service_Icons_V23.zip` | Ícones oficiais de serviço Azure (v23), organizados por categoria | Fallback/conferência para ícones azure2 já usados; fonte para categorias não cobertas pela lib embutida do draw.io |
| `Power-Platform-icons-scalable.zip` | Ícones oficiais Power Platform (Power Apps, Power Automate, Power Pages, Dataverse, Copilot Studio, AI Builder) | Diagramas que envolvem Power Platform — sem equivalente na lib azure2 |
| `2024-microsoft-365-content-icons.zip` | Ícones oficiais M365 (Teams, SharePoint, Outlook, etc., múltiplas variações de cor/tamanho) | Diagramas com componentes M365 (ex.: SharePoint Online, Teams Apps) — hoje representados como cards cinza sem ícone; esses pacotes permitem evoluir para ícone oficial embutido via base64/data URI quando necessário |

Regra de uso: preferir sempre a lib `azure2` embutida do draw.io (validada via HTTP 200) quando o serviço é nativamente Azure. Só recorrer a estes pacotes locais quando o serviço pertence a M365/Power Platform (fora do catálogo azure2) — nesse caso, extrair o SVG necessário do zip, embutir como `image=data:image/svg+xml;base64,...` no estilo do nó, e marcar na legenda com `*` (AZD-403, proxy/fonte alternativa).

## 0.2 Taxonomia de códigos de regra (AZD-xxx)

Toda violação encontrada durante autocorreção ou revisão deve ser referenciada pelo código, não só descrita em prosa — facilita rastrear "o que foi corrigido" entre versões de um diagrama e comunicar qualidade de forma objetiva (ex.: em um relatório de entrega: "0 violações AZD abertas").

| Faixa | Categoria | Códigos principais |
|---|---|---|
| `AZD-0xx` | Pipeline / setup | `001` Mermaid ausente ou não salvo como `.mmd` · `002` layout copiou coordenadas literais do Mermaid em vez de semântico · `003` conteúdo fora de EN-US |
| `AZD-1xx` | Canvas & camadas | `101` proporção ≠ 16:9 · `102` faltam as 4 camadas nomeadas (Zones/Connectors/Nodes/Annotations) · `103` falta a camada padrão `id="1" parent="0"` · `104` conteúdo estourando a página |
| `AZD-2xx` | Estilo visual | `201` cor usada sem significado semântico definido · `202` ícone de serviço sem rótulo dentro da célula · `203` rótulo de nó > 3 linhas ou > 18 caracteres/linha · `204` tamanho de ícone inconsistente entre nós |
| `AZD-3xx` | Anti-sobreposição | `301` seta cruza texto (rótulo, título de zona, legenda) · `302` aresta sem `exitX/exitY/entryX/entryY` explícitos · `303` cruzamento seta×seta não-perpendicular ou evitável · `304` setas paralelas sem offset mínimo |
| `AZD-4xx` | Ícones | `401` ícone não validado (sem checagem HTTP 200) · `402` uso da biblioteca `mscae` (não servida como imagem) · `403` proxy usado sem marcação `*` na legenda |
| `AZD-5xx` | Layout & narrativa | `501` layout reproduz sintaxe do Mermaid em vez de narrativa de negócio · `502` mais de 6 componentes em uma região sem contêiner · `503` whitespace abaixo de 40% · `504` mais de um fluxo dominante competindo visualmente · `505` exceção/revisão humana não isolada do fluxo principal |
| `AZD-6xx` | Idioma & legenda | `601` termo fora da terminologia oficial Microsoft · `602` legenda ausente ou incompleta para ícones/proxies usados |

Uso esperado: ao autocorrigir um "smell" (seção 6), citar o código (ex.: "corrigido AZD-301: rótulo 'Baixa < 70%' cruzava a seta principal — reancorado"). Ao validar um diagrama existente sem regenerar, produzir uma lista de códigos abertos em vez de reescrever tudo.

## 0.3 Seleção de modo (antes de desenhar)

Antes de iniciar a reconstrução narrativa (§6), classificar explicitamente o cenário em um modo — isso decide o esquema de cores dos conectores (já existente, seção 6) e o padrão de zonas a aplicar. Não é uma pergunta ao usuário por padrão; é uma decisão que o próprio processo de geração faz e pode declarar em uma linha antes de compor o XML (ex.: "Modo: Architecture — sistema com camadas de serviço").

| Modo | Quando usar | Paleta de conectores | Exemplo já implementado |
|---|---|---|---|
| **Flowchart** | Decisão/status: aprovação, triagem, roteamento com branches Sim/Não | cinza=fluxo normal, vermelho=exceção, vermelho tracejado=baixa confiança, laranja=escalação, roxo tracejado=retorno de retry/revisão | `email-triage-copilot.drawio`, `legal-document-automation.drawio` |
| **Architecture** | Topologia de sistema: camadas de serviço, dados, integração | cinza=negócio, teal=dados/IA, roxo=integração, laranja=eventos/mensageria, cinza tracejado=cross-cutting | `sales-quoting-mvp-architecture.drawio`, `agentic-platform-architecture.drawio` |
| **Sequence** *(roadmap — ainda não implementado)* | Interações temporais entre atores/serviços (chamadas de API, ordem estrita) | — | — |
| **Data Flow** *(roadmap — ainda não implementado)* | Pipelines de dados, linhagem, limites de sensibilidade | — | — |
| **Lifecycle** *(roadmap — ainda não implementado)* | Estados e transições (retry, terminal states) | — | — |

Um diagrama pode combinar os dois modos implementados quando há um processo de negócio com um "miolo" de arquitetura de sistema (como aconteceu no Legal Document Automation: fluxo decisório com nós de IA identificados por cor arquitetural). Nesse caso, o modo dominante é Flowchart e a paleta arquitetural é usada apenas nos nós/arestas que representam integração de dados (regra já existente, seção 6, "Cores de conector").

## 0. Ferramenta e pipeline
- **MCP oficial do draw.io** registrado no Claude Code (escopo usuário): `drawio` → `https://mcp.draw.io/mcp` (Streamable HTTP). Usar as ferramentas desse MCP quando disponíveis na sessão; caso contrário, gerar o XML `.drawio` diretamente (mesmo formato). Alternativa local: `npx -y @drawio/mcp` (pacote oficial `jgraph/drawio-mcp`, suporta XML draw.io, CSV e Mermaid).
- **O Mermaid é a fonte lógica da verdade**; o layout é semântico, nunca a posição literal do Mermaid. Guardar o `.mmd` de origem junto do `.drawio`.
- Usar **nomes oficiais dos serviços Microsoft/Azure** nos rótulos.
- Pipeline: `Mermaid/descrição → layout semântico → .drawio nativo editável → validação (MCP create_diagram + revisão visual) → render final em app.diagrams.net → exportes (SVG/PNG/PDF/PPT)`.
- Validar que cada ícone, rótulo e conector está ligado ao componente correto antes de entregar (revisão visual renderizada obrigatória).
- **Render final obrigatório em `https://app.diagrams.net/`**: após o diagrama passar na validação estrutural (MCP `create_diagram`) e na revisão visual (screenshot), abrir o `.drawio` final diretamente no editor web oficial para entrega interativa/editável ao usuário — não apenas a prévia estática. Método: gerar uma página HTML local com `window.location.replace("https://app.diagrams.net/?splash=0#R" + encodeURIComponent(xml))`, servir via `python3 -m http.server` numa porta livre, e navegar até ela no Browser pane (o fragmento `#R<xml>` evita colar o XML inteiro na URL do `navigate`, que tem limite de tamanho). Ao final, ajustar `Ctrl/Cmd+Shift+H` para caber a página na tela. Encerrar o servidor local depois que a página carregar (o diagrama já ficou no estado do navegador).

## 0.1 Idioma
- **Todo o conteúdo do diagrama é EN-US** (rótulos de nós e arestas, títulos de zonas, legenda, título) — os projetos são 100% EN-US. A conversa com o usuário permanece em PT-BR.

## 1. Canvas e formato (AZD-1xx)
- **Sempre 16:9** para uso em PPT: `pageWidth="1600" pageHeight="900"`, margens de 40px. *(AZD-101)*
- Todo o conteúdo deve caber em uma única página, sem estouro. *(AZD-104)*
- Fundo branco, sem grid visível na exportação.

## 2. Camadas (obrigatório) (AZD-102 / AZD-103)
Todo diagrama usa 4 camadas draw.io, nesta ordem de empilhamento (de baixo para cima):
1. `Zonas` — contêineres pontilhados de agrupamento
2. `Conectores` — todas as setas
3. `Nós` — ícones + rótulos e formas de decisão
4. `Anotações` — badges numerados, título, legenda, logo

Mais a camada padrão `<mxCell id="1" parent="0"/>`, exigida pelo validador do MCP oficial (AZD-103).

## 3. Estilo visual (cards coloridos + Architecture Center)
- **Zonas**: retângulo sem preenchimento, borda pontilhada cinza claro (`dashed=1;dashPattern=1 2;strokeColor=#999999`), título centralizado no topo, fontSize 13.
- **Nós de serviço**: CARD arredondado (`rounded=1;arcSize=12`) com borda colorida e preenchimento suave, ícone oficial Azure2 (40px) no topo e rótulo abaixo, tudo DENTRO da mesma célula (`shape=label;imageAlign=center;imageVerticalAlign=top;verticalAlign=bottom`), célula 130×96.
- **Semântica de cores** (borda / preenchimento):
  - Verde `#2E9E4F / #F1FAF4` — início, fim, confirmações, caminho feliz
  - Azul `#2E77D0 / #F2F7FD` — processos padrão
  - Roxo `#7C4DC4 / #F7F3FC` — IA, retry, analista, Power Apps
  - Laranja `#E8871A / #FEF7EF` — escalação, triagem manual, regras de negócio, log de override
  - Vermelho `#D64550 / #FDF3F4` — filas de exceção e falhas
- **Decisões**: losango branco com borda na cor do contexto (azul principal, roxo IA/analista, laranja negócio).
- **Terminais**: pills arredondados verdes ("Fim"; início pode ser card verde).
- **Setas**: ortogonais `strokeWidth=1.5`, cinza-escuro `#333333` no fluxo normal; **vermelhas** nos fluxos de exceção; **vermelha tracejada** para baixa confiança; **laranja** para escalação/revisão manual; **roxa tracejada** para retornos de retry ao fluxo principal.
- **Rótulos de aresta coloridos e em negrito**: "Sim/Aprovado/Alta" verde, "Não/Baixa" vermelho, "Média/Revisão manual" laranja, ações de analista roxo/azul — sempre com `labelBackgroundColor=#FFFFFF` e ancorados perto da origem.
- **Faixa de legenda** no rodapé: caixa pontilhada com mini-ícones (20px) + nome oficial de cada serviço usado; proxies marcados com `*`.
- Filas de exceção usam o ícone **Service Bus** (semântica de fila), com card vermelho indicando falha.
- Título no topo esquerdo; assinatura "Microsoft Azure · Power Platform" no topo direito.
- Badges numerados são opcionais (usar apenas se o público precisar de narração sequencial; o padrão atual transmite a semântica pelas cores).

## 4. Anti-sobreposição (obrigatório) (AZD-3xx)
- **Seta nunca cruza texto** (rótulo de nó, título de zona, badge ou legenda). Como o rótulo fica dentro da célula do nó, as setas conectam na borda da célula — abaixo do texto. *(AZD-301)*
- Saídas/entradas de setas sempre com `exitX/exitY/entryX/entryY` explícitos *(AZD-302)*; rotas longas com waypoints explícitos por **corredores livres**: faixas horizontais/verticais reservadas entre zonas (ex.: y≈490–505 entre a faixa principal e a faixa de exceções; gaps de 20px entre zonas).
- Rótulos de aresta ("Sim"/"Não") curtos, com `labelBackgroundColor=#FFFFFF`, posicionados junto à origem da seta.
- Cruzamento seta×seta: apenas perpendicular e no máximo quando inevitável *(AZD-303)*; nunca setas paralelas sobrepostas (offset mínimo de 10px) *(AZD-304)*.
- Retornos longos são roteados por FORA das zonas (por baixo ou pelas laterais), como no modelo de referência.

## 5. Ícones — validar antes de usar (AZD-4xx)
- Conjunto: **Azure2** embutido no draw.io (`img/lib/azure2/<categoria>/<Nome>.svg`).
- Validar cada caminho com `curl -s -o /dev/null -w "%{http_code}" https://app.diagrams.net/<path>` — usar somente os que retornam 200. *(AZD-401)*
- A biblioteca `mscae` NÃO está disponível como imagem (404) — nunca usar. *(AZD-402)*
- **Descoberta de ícones**: usar a ferramenta `search_shapes` do MCP do draw.io para encontrar o shape oficial antes de recorrer a proxy (foi assim que se descobriu a categoria `azure2/power_platform`).
- Ícones OFICIAIS validados (200):

| Serviço | Ícone oficial (validado 200) |
|---|---|
| Copilot Studio | `img/lib/azure2/power_platform/CopilotStudio.svg` |
| Dataverse | `img/lib/azure2/power_platform/Dataverse.svg` |
| Power Apps | `img/lib/azure2/power_platform/PowerApps.svg` |
| Power Automate | `img/lib/azure2/power_platform/PowerAutomate.svg` |
| Azure OpenAI / LLM | `img/lib/azure2/ai_machine_learning/Azure_OpenAI.svg` |
| Log Analytics | `img/lib/azure2/analytics/Log_Analytics_Workspaces.svg` |
| Notification Hubs | `img/lib/azure2/app_services/Notification_Hubs.svg` |

- Proxies para serviços ainda sem ícone-imagem próprio:

| Serviço | Ícone proxy (validado 200) |
|---|---|
| Microsoft Graph | `img/lib/azure2/identity/Azure_Active_Directory.svg` (há stencil `mxgraph.mscae.general.graph`, mas rótulo fica fora da célula — evitar) |
| Shared Mailbox / e-mail | `img/lib/azure2/other/Azure_Communication_Services.svg` |
| Fila de exceção / erro | `img/lib/azure2/general/Error.svg` |
| Retry / agendamento | `img/lib/azure2/general/Recent.svg` |
| Usuário / analista | `img/lib/azure2/identity/Users.svg` |

- Todo proxy usado deve constar em legenda discreta no diagrama. *(AZD-403 / AZD-602)*
- O XML deve conter a camada padrão `<mxCell id="1" parent="0"/>` além das 4 camadas nomeadas (exigência do validador do MCP oficial). *(AZD-103)*

## 6. Layout (anti-desordem + narrativa) (AZD-5xx)
- **Narrativa primeiro** (fonte: "Azure Enterprise Architecture Design System" v1.0, PDF do usuário): entender o processo de negócio → identificar a narrativa primária → separar processos de apoio → separar exceções → separar preocupações operacionais → só então desenhar. O layout comunica a jornada de negócio, não a sintaxe do Mermaid *(AZD-501)*. Teste dos 5 segundos: um CIO entende o fluxo sem ler os rótulos.
- Fluxo principal **esquerda → direita** na faixa superior, agrupado em zonas por fase (máx. 4–5 zonas); UM fluxo dominante por diagrama — fluxos secundários nunca competem visualmente *(AZD-504)*.
- Exceções e revisão humana em faixa inferior própria, atravessando a largura; revisão humana isolada (inferior-direita/centro) *(AZD-505)*; retry agrupado e próximo da operação que protege; monitoramento/governança sempre periféricos.
- **Densidade**: 3–6 serviços por região visual (>6 → dividir ou criar contêiner) *(AZD-502)*; nunca zonas/contêineres vazios. **Whitespace alvo 40–55%** — expandir o layout em vez de comprimir *(AZD-503)*.
- **Aproveitamento do template (canvas 16:9)**: usar a área útil de forma harmônica e centralizada — zonas distribuídas para preencher a largura/altura do canvas sem deixar grandes vazios de um lado e aglomeração do outro; margens e espaçamento entre zonas visualmente equilibrados (não apenas funcionalmente corretos). Preferir redistribuir as zonas existentes (larguras/alturas/posições) a criar zonas novas só para "usar espaço".
- **Mínimo de edição possível**: ao ajustar um diagrama já validado (correção de overlap, rebalanceamento de espaço, etc.), mudar apenas o necessário — reposicionar/redimensionar as células afetadas, não recompor o XML do zero. Preserva histórico de revisão e reduz risco de introduzir novas violações AZD em partes que já estavam corretas.
- **Conectores sem overengineering**: uma aresta por relação lógica do Mermaid, sem waypoints extras além do mínimo para evitar sobreposição (AZD-301/AZD-304). Não adicionar labels, cores ou desvios "decorativos" a um conector que uma linha reta ou ortogonal simples já resolve. Se uma aresta precisa de mais de 2 waypoints para não cruzar nada, é sinal de reposicionar as zonas/nós envolvidos, não de complicar a rota.
- **Rótulos**: máx. 3 linhas × ~18 caracteres/linha, terminologia oficial Microsoft, nomes e não descrições *(AZD-203 / AZD-601)*.
- **Cores de conector em modo arquitetura** (topologia de serviços): cinza-escuro = fluxo de negócio; teal = dados/IA; roxo = integração; laranja = eventos/mensageria; cinza tracejado = segurança/governança/monitoramento (cross-cutting). O modo flowchart (status: verde/vermelho/laranja) continua valendo para fluxos decisórios.
- **Smells para autocorreção**: setas cruzadas, serviços duplicados, ícones desalinhados, espaçamento irregular, contêineres superdimensionados, regiões lotadas ou vazias, tamanhos de ícone inconsistentes, rótulos longos, fluxos competindo.
- **Scorecard final**: alinhamento de grade, equilíbrio visual, whitespace, organização de zonas, clareza do fluxo primário, separação de exceções, simplicidade de conectores, estilo Microsoft, ícones oficiais e legibilidade executiva — tudo 10/10 antes de entregar.
- Verificação final obrigatória: renderizar no viewer (preview.html) e inspecionar screenshot antes de entregar.
