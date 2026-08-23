import "./index.css";
import { parseMedia } from "@remotion/media-parser";
import { Composition, staticFile } from "remotion";
import { Audiogram } from "./Audiogram/Main";
import { audiogramSchema } from "./Audiogram/schema";
import { getSubtitles } from "./helpers/fetch-captions";
import { FPS } from "./helpers/ms-to-frame";
import { AzureMigrationFactory } from "./AzureMigrationFactory/Main";
import { azureMigrationFactorySchema } from "./AzureMigrationFactory/schema";
import {
  FPS as AMF_FPS,
  HEIGHT as AMF_HEIGHT,
  TOTAL_DURATION_IN_FRAMES,
  WIDTH as AMF_WIDTH,
} from "./AzureMigrationFactory/data";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AzureMigrationFactory"
        component={AzureMigrationFactory}
        width={AMF_WIDTH}
        height={AMF_HEIGHT}
        fps={AMF_FPS}
        durationInFrames={TOTAL_DURATION_IN_FRAMES}
        schema={azureMigrationFactorySchema}
        defaultProps={{
          showDirectorNotes: true,
          act1VideoUrl: null,
          act2VideoUrl: null,
          act3VideoUrl: null,
          act4VideoUrl: null,
          act5VideoUrl: null,
          voAudioUrl: null,
          musicUrl: null,
        }}
      />
      <Composition
        id="Audiogram"
        component={Audiogram}
        width={1080}
        height={1080}
        schema={audiogramSchema}
        defaultProps={{
          // audio settings
          audioOffsetInSeconds: 0,
          audioFileUrl: staticFile("dialogue.wav"),
          // podcast data
          coverImageUrl: staticFile("podcast-cover.jpeg"),
          titleText: "Ep 550 - Supper Club × Remotion React",
          titleColor: "rgba(186, 186, 186, 0.93)",
          // captions settings
          captions: null,
          captionsFileName: staticFile("captions.json"),
          onlyDisplayCurrentSentence: true,
          captionsTextColor: "rgba(255, 255, 255, 0.93)",
          // visualizer settings
          visualizer: {
            type: "oscilloscope",
            color: "#F4B941",
            numberOfSamples: "64" as const,
            windowInSeconds: 0.1,
            posterization: 3,
            amplitude: 4,
            padding: 50,
          },
        }}
        // Determine the length of the video based on the duration of the audio file
        calculateMetadata={async ({ props }) => {
          const captions = await getSubtitles(props.captionsFileName);
          const { slowDurationInSeconds } = await parseMedia({
            src: props.audioFileUrl,
            acknowledgeRemotionLicense: true,
            fields: {
              slowDurationInSeconds: true,
            },
          });

          return {
            durationInFrames: Math.floor(
              (slowDurationInSeconds - props.audioOffsetInSeconds) * FPS,
            ),
            props: {
              ...props,
              captions,
            },
            fps: FPS,
          };
        }}
      />
    </>
  );
};
