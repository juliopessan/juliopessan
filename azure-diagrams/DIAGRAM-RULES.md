# Regras — Diagramas Azure em draw.io (padrão Microsoft Architecture Center)

Regras obrigatórias para TODA geração de diagramas `.drawio` a partir de Mermaid ou descrição de arquitetura. Modelo de referência: `reference.svg` (Microsoft Architecture Center).

## 0. Ferramenta e pipeline
- **MCP oficial do draw.io** registrado no Claude Code (escopo usuário): `drawio` → `https://mcp.draw.io/mcp` (Streamable HTTP). Usar as ferramentas desse MCP quando disponíveis na sessão; caso contrário, gerar o XML `.drawio` diretamente (mesmo formato). Alternativa local: `npx -y @drawio/mcp` (pacote oficial `jgraph/drawio-mcp`, suporta XML draw.io, CSV e Mermaid).
- **O Mermaid é a fonte lógica da verdade**; o layout é semântico, nunca a posição literal do Mermaid. Guardar o `.mmd` de origem junto do `.drawio`.
- Usar **nomes oficiais dos serviços Microsoft/Azure** nos rótulos.
- Pipeline: `Mermaid/descrição → layout semântico → .drawio nativo editável → exportes (SVG/PNG/PDF/PPT)`.
- Validar que cada ícone, rótulo e conector está ligado ao componente correto antes de entregar (revisão visual renderizada obrigatória).

## 0.1 Idioma
- **Todo o conteúdo do diagrama é EN-US** (rótulos de nós e arestas, títulos de zonas, legenda, título) — os projetos são 100% EN-US. A conversa com o usuário permanece em PT-BR.

## 1. Canvas e formato
- **Sempre 16:9** para uso em PPT: `pageWidth="1600" pageHeight="900"`, margens de 40px.
- Todo o conteúdo deve caber em uma única página, sem estouro.
- Fundo branco, sem grid visível na exportação.

## 2. Camadas (obrigatório)
Todo diagrama usa 4 camadas draw.io, nesta ordem de empilhamento (de baixo para cima):
1. `Zonas` — contêineres pontilhados de agrupamento
2. `Conectores` — todas as setas
3. `Nós` — ícones + rótulos e formas de decisão
4. `Anotações` — badges numerados, título, legenda, logo

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

## 4. Anti-sobreposição (obrigatório)
- **Seta nunca cruza texto** (rótulo de nó, título de zona, badge ou legenda). Como o rótulo fica dentro da célula do nó, as setas conectam na borda da célula — abaixo do texto.
- Saídas/entradas de setas sempre com `exitX/exitY/entryX/entryY` explícitos; rotas longas com waypoints explícitos por **corredores livres**: faixas horizontais/verticais reservadas entre zonas (ex.: y≈490–505 entre a faixa principal e a faixa de exceções; gaps de 20px entre zonas).
- Rótulos de aresta ("Sim"/"Não") curtos, com `labelBackgroundColor=#FFFFFF`, posicionados junto à origem da seta.
- Cruzamento seta×seta: apenas perpendicular e no máximo quando inevitável; nunca setas paralelas sobrepostas (offset mínimo de 10px).
- Retornos longos são roteados por FORA das zonas (por baixo ou pelas laterais), como no modelo de referência.

## 5. Ícones — validar antes de usar
- Conjunto: **Azure2** embutido no draw.io (`img/lib/azure2/<categoria>/<Nome>.svg`).
- Validar cada caminho com `curl -s -o /dev/null -w "%{http_code}" https://app.diagrams.net/<path>` — usar somente os que retornam 200.
- A biblioteca `mscae` NÃO está disponível como imagem (404) — nunca usar.
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

- Todo proxy usado deve constar em legenda discreta no diagrama.
- O XML deve conter a camada padrão `<mxCell id="1" parent="0"/>` além das 4 camadas nomeadas (exigência do validador do MCP oficial).

## 6. Layout (anti-desordem + narrativa)
- **Narrativa primeiro** (fonte: "Azure Enterprise Architecture Design System" v1.0, PDF do usuário): entender o processo de negócio → identificar a narrativa primária → separar processos de apoio → separar exceções → separar preocupações operacionais → só então desenhar. O layout comunica a jornada de negócio, não a sintaxe do Mermaid. Teste dos 5 segundos: um CIO entende o fluxo sem ler os rótulos.
- Fluxo principal **esquerda → direita** na faixa superior, agrupado em zonas por fase (máx. 4–5 zonas); UM fluxo dominante por diagrama — fluxos secundários nunca competem visualmente.
- Exceções e revisão humana em faixa inferior própria, atravessando a largura; revisão humana isolada (inferior-direita/centro); retry agrupado e próximo da operação que protege; monitoramento/governança sempre periféricos.
- **Densidade**: 3–6 serviços por região visual (>6 → dividir ou criar contêiner); nunca zonas/contêineres vazios. **Whitespace alvo 40–55%** — expandir o layout em vez de comprimir.
- **Rótulos**: máx. 3 linhas × ~18 caracteres/linha, terminologia oficial Microsoft, nomes e não descrições.
- **Cores de conector em modo arquitetura** (topologia de serviços): cinza-escuro = fluxo de negócio; teal = dados/IA; roxo = integração; laranja = eventos/mensageria; cinza tracejado = segurança/governança/monitoramento (cross-cutting). O modo flowchart (status: verde/vermelho/laranja) continua valendo para fluxos decisórios.
- **Smells para autocorreção**: setas cruzadas, serviços duplicados, ícones desalinhados, espaçamento irregular, contêineres superdimensionados, regiões lotadas ou vazias, tamanhos de ícone inconsistentes, rótulos longos, fluxos competindo.
- **Scorecard final**: alinhamento de grade, equilíbrio visual, whitespace, organização de zonas, clareza do fluxo primário, separação de exceções, simplicidade de conectores, estilo Microsoft, ícones oficiais e legibilidade executiva — tudo 10/10 antes de entregar.
- Verificação final obrigatória: renderizar no viewer (preview.html) e inspecionar screenshot antes de entregar.
