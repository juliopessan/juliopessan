import React from "react";
import { AbsoluteFill, Audio, Sequence } from "remotion";
import { ACT_1_TO_2_CUT_FRAME, acts } from "./data";
import { Scene } from "./Scene";
import { WhipCut } from "./WhipCut";
import type { AzureMigrationFactorySchemaType } from "./schema";

const actVideoProp = {
  1: "act1VideoUrl",
  2: "act2VideoUrl",
  3: "act3VideoUrl",
  4: "act4VideoUrl",
  5: "act5VideoUrl",
} as const;

const WHIP_CUT_DURATION = 8;

export const AzureMigrationFactory: React.FC<AzureMigrationFactorySchemaType> = (props) => {
  const { showDirectorNotes, voAudioUrl, musicUrl } = props;

  return (
    <AbsoluteFill style={{ backgroundColor: "#020409" }}>
      {musicUrl ? <Audio src={musicUrl} volume={0.8} /> : null}
      {voAudioUrl ? <Audio src={voAudioUrl} volume={1} /> : null}

      {acts.map((act) => (
        <Sequence key={act.id} from={act.startFrame} durationInFrames={act.durationInFrames}>
          <Scene act={act} videoSrc={props[actVideoProp[act.id]]} showDirectorNotes={showDirectorNotes} />
        </Sequence>
      ))}

      <Sequence from={ACT_1_TO_2_CUT_FRAME - WHIP_CUT_DURATION / 2} durationInFrames={WHIP_CUT_DURATION}>
        <WhipCut durationInFrames={WHIP_CUT_DURATION} />
      </Sequence>
    </AbsoluteFill>
  );
};
