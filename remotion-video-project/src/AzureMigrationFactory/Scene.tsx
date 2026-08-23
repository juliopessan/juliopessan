import React from "react";
import { AbsoluteFill, OffthreadVideo, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Act } from "./data";
import { Placeholder } from "./Placeholder";

const EMBER = "#ff8a3d";
const AZURE = "#5fb3ff";

export const Scene: React.FC<{
  act: Act;
  videoSrc: string | null;
  showDirectorNotes: boolean;
}> = ({ act, videoSrc, showDirectorNotes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 20 });
  const exitStart = act.durationInFrames - 15;
  const exit = interpolate(frame, [exitStart, act.durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(entrance, exit);
  const translateY = interpolate(entrance, [0, 1], [24, 0]);

  return (
    <AbsoluteFill>
      {videoSrc ? (
        <OffthreadVideo src={videoSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <Placeholder act={act} />
      )}

      {/* Bottom gradient for caption legibility over any footage */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, transparent 0%, transparent 55%, rgba(2,4,9,0.55) 78%, rgba(2,4,9,0.88) 100%)",
        }}
      />

      {/* Act label chip */}
      <div
        style={{
          position: "absolute",
          top: 48,
          left: 56,
          display: "flex",
          alignItems: "center",
          gap: 12,
          opacity,
        }}
      >
        <div style={{ width: 4, height: 22, background: EMBER, borderRadius: 2 }} />
        <span
          style={{
            fontFamily: "monospace",
            fontSize: 16,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.7)",
          }}
        >
          {act.label} · {act.timecode}
        </span>
      </div>

      {/* VO caption */}
      <div
        style={{
          position: "absolute",
          left: 56,
          right: 220,
          bottom: 72,
          opacity,
          transform: `translateY(${translateY}px)`,
        }}
      >
        <p
          style={{
            fontFamily: "Georgia, 'Times New Roman', serif",
            fontSize: 44,
            lineHeight: 1.3,
            color: "white",
            textShadow: "0 2px 24px rgba(0,0,0,0.6)",
            margin: 0,
            maxWidth: 1200,
          }}
        >
          {act.voText}
        </p>
      </div>

      {showDirectorNotes ? (
        <div
          style={{
            position: "absolute",
            top: 48,
            right: 48,
            width: 420,
            padding: "14px 18px",
            border: `1px dashed rgba(255,255,255,0.25)`,
            borderRadius: 10,
            background: "rgba(2,4,9,0.35)",
            opacity: opacity * 0.9,
          }}
        >
          <div
            style={{
              fontFamily: "monospace",
              fontSize: 11,
              letterSpacing: 2,
              textTransform: "uppercase",
              color: AZURE,
              marginBottom: 6,
            }}
          >
            Nota de direção
          </div>
          <p
            style={{
              fontFamily: "system-ui, sans-serif",
              fontSize: 13,
              lineHeight: 1.5,
              color: "rgba(255,255,255,0.75)",
              margin: 0,
            }}
          >
            {act.direction}
          </p>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: 12,
              color: EMBER,
              marginTop: 10,
            }}
          >
            {act.musicCue}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
