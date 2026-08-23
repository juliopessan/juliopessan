export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

export type Act = {
  id: 1 | 2 | 3 | 4 | 5;
  label: string;
  timecode: string;
  startFrame: number;
  durationInFrames: number;
  voText: string;
  direction: string;
  musicCue: string;
};

/**
 * Timing matches the client-approved script exactly (5+7+6+7+5 = 30s @ 30fps).
 * Do not rebalance frame counts without updating the script's timecodes too.
 */
export const acts: Act[] = [
  {
    id: 1,
    label: "Ato 1 — O Gancho",
    timecode: "0:00–0:05",
    startFrame: 0,
    durationInFrames: 5 * FPS,
    voText:
      "Neste exato momento, nossa maior barreira para o crescimento não é o mercado. É a nossa própria fundação.",
    direction:
      "107° wide rectilinear, câmera a 60cm da mesa de vidro. Holograma de datacenter legado em primeiro plano. Arquiteto aponta para os data streams emaranhados. Push-in físico rápido até o holograma passar sobre a lente.",
    musicCue: "Baixo tenso e denso (sintetizadores pesados)",
  },
  {
    id: 2,
    label: "Ato 2 — A Lentidão Manual",
    timecode: "0:05–0:12",
    startFrame: 5 * FPS,
    durationInFrames: 7 * FPS,
    voText:
      "Entender sistemas legados de forma manual consome meses. E migrações baseadas em suposições estouram prazos e orçamentos.",
    direction:
      "Whip cut / match cut através de um portal azul digital para um data center surreal. HD físico atravessa um rack e vira holograma de dados Azure nas mãos de outra arquiteta. Órbita 180° enquanto ela dispersa o holograma.",
    musicCue: "Baixo tenso e denso (mantém)",
  },
  {
    id: 3,
    label: "Ato 3 — Engenharia Determinística",
    timecode: "0:12–0:18",
    startFrame: 12 * FPS,
    durationInFrames: 6 * FPS,
    voText:
      "Mudamos a abordagem. Mapeamos a infraestrutura de forma determinística e desenhamos o futuro no Azure antes de construí-lo.",
    direction:
      "Overhead shot: quatro arquitetos em composição radial ao redor de mesa circular de arquitetura. Macro cuts (18°): fibra óptica acendendo em azul, nó Azure formando geometria perfeita, dedos digitando substituindo código legado por estruturas Azure.",
    musicCue: "Trilha abre — limpa, inspiradora, rítmica",
  },
  {
    id: 4,
    label: "Ato 4 — O Valor de Negócio",
    timecode: "0:18–0:25",
    startFrame: 18 * FPS,
    durationInFrames: 7 * FPS,
    voText:
      "O resultado? Governança de ponta a ponta, otimização exata de custos e a plataforma perfeita para escalar Inteligência Artificial.",
    direction:
      "Low-angle hero shot, 107° wide, altura do chão. Quatro arquitetos em diamante ao redor do pedestal Azure. Líder cruza a lente, câmera guinda para cima. Expressões mudam de foco analítico para sorrisos confiantes.",
    musicCue: "Inspiradora, rítmica (mantém)",
  },
  {
    id: 5,
    label: "Ato 5 — Call to Action",
    timecode: "0:25–0:30",
    startFrame: 25 * FPS,
    durationInFrames: 5 * FPS,
    voText: "Não é apenas uma mudança de data center. É velocidade de mercado. Vamos migrar.",
    direction:
      "Group shot para packshot, 84° wide, dolly curvo rápido. Tablets holográficos sincronizados no centro. Hard cut para packshot: nó de arquitetura Azure em pedestal espelhado, push-in de 29° com paralaxe sutil.",
    musicCue: "Chime de ativação digital no swipe sincronizado dos tablets",
  },
];

export const TOTAL_DURATION_IN_FRAMES = acts.reduce((sum, act) => sum + act.durationInFrames, 0);

/** Frame at which Act 1 cuts to Act 2 — used to place the whip-cut transition. */
export const ACT_1_TO_2_CUT_FRAME = acts[0].startFrame + acts[0].durationInFrames;
