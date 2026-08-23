import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

/**
 * Short directional-blur flash used at the Act 1 -> Act 2 boundary to sell
 * the "WHIP CUT to MATCH CUT" beat from the script. Rendered on top of both
 * scenes for a handful of frames centered on the cut.
 */
export const WhipCut: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const progress = frame / Math.max(durationInFrames - 1, 1);

  const streakOpacity = interpolate(progress, [0, 0.4, 1], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const streakX = interpolate(progress, [0, 1], [-30, 130]);
  const flashOpacity = interpolate(progress, [0, 0.35, 0.5, 1], [0, 0.55, 0.2, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ background: "white", opacity: flashOpacity }} />
      <div
        style={{
          position: "absolute",
          top: "-10%",
          left: `${streakX}%`,
          width: "35%",
          height: "120%",
          transform: "skewX(-18deg)",
          background:
            "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.9) 45%, rgba(95,179,255,0.9) 55%, transparent 100%)",
          filter: "blur(6px)",
          opacity: streakOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
