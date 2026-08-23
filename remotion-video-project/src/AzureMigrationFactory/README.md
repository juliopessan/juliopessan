# AzureMigrationFactory

Montagem executiva de 30s ("The Azure Migration Factory") em 5 atos, com
timing sincronizado ao roteiro em `BRIEF.md`. Composição registrada em
`src/Root.tsx` com id `AzureMigrationFactory` (1920×1080, 30fps, 900 frames).

Enquanto não há footage real, cada ato renderiza um placeholder estilizado
(navy/azure/ember, `Placeholder.tsx`) com a legenda de VO já animada em tela
e — opcionalmente — uma nota de direção (câmera + trilha) sobreposta, útil
para revisão interna.

## Como plugar os clipes gerados por IA

1. Gere os 5 clipes (Runway, Sora, Veo, Kling, etc.) usando os prompts de
   câmera em `BRIEF.md`, um por ato.
2. Salve-os em `public/azure-migration-factory/` com esses nomes:
   - `act-1.mp4` … `act-5.mp4`
   - `vo-pt.mp3` (locução) e `score.mp3` (trilha), se já gravados
3. No Remotion Studio (`npm run dev`), abra a composição
   `AzureMigrationFactory` e preencha os campos de props (`act1VideoUrl`,
   `voAudioUrl`, etc.) com `staticFile("azure-migration-factory/act-1.mp4")`
   — ou edite os `defaultProps` direto em `src/Root.tsx`.
4. Desligue `showDirectorNotes` antes do render final (fica ligado por
   padrão, é só para revisão/previz).

## Renderizar

```
npx remotion render AzureMigrationFactory out/azure-migration-factory.mp4
```
