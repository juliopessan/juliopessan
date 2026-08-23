import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Act } from "./data";

const NAVY_DEEP = "#050a14";
const NAVY = "#0a1628";
const AZURE = "#2f8fff";
const EMBER = "#ff8a3d";

/**
 * Stylized stand-in background so the composition has a coherent look
 * before the real AI-generated footage for an act is dropped in. Swap it
 * out by passing a video URL for that act via the composition props.
 */
export const Placeholder: React.FC<{ act: Act }> = ({ act }) => {
  const frame = useCurrentFrame();

  const sweepX = interpolate(frame, [0, act.durationInFrames], [-40, 140], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const glowDrift = interpolate(frame, [0, act.durationInFrames], [0, 24], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 90% at 20% 15%, ${NAVY} 0%, ${NAVY_DEEP} 55%, #020409 100%)`,
        overflow: "hidden",
      }}
    >
      {/* Azure glow, drifting slowly */}
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          left: `${30 + glowDrift * 0.3}%`,
          top: "-10%",
          background: `radial-gradient(circle, ${AZURE}33 0%, transparent 70%)`,
          filter: "blur(10px)",
        }}
      />
      {/* Ember accent glow */}
      <div
        style={{
          position: "absolute",
          width: 700,
          height: 700,
          borderRadius: "50%",
          right: `${10 - glowDrift * 0.2}%`,
          bottom: "-15%",
          background: `radial-gradient(circle, ${EMBER}22 0%, transparent 70%)`,
          filter: "blur(10px)",
        }}
      />
      {/* Diagonal light sweep, premium tech-commercial style */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: `${sweepX}%`,
          width: "20%",
          height: "160%",
          transform: "rotate(18deg)",
          background:
            "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 45%, rgba(47,143,255,0.12) 50%, rgba(255,255,255,0.05) 55%, transparent 100%)",
        }}
      />
      {/* Faint act watermark for orientation while previewing */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontFamily: "monospace",
            fontSize: 340,
            fontWeight: 700,
            color: "rgba(255,255,255,0.035)",
            letterSpacing: -10,
          }}
        >
          {String(act.id).padStart(2, "0")}
        </span>
      </AbsoluteFill>
      {/* Grain */}
      <svg
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.05 }}
      >
        <filter id={`grain-${act.id}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${act.id})`} />
      </svg>
      {/* Placeholder stamp, clearly marking this isn't final footage */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          right: 48,
          fontFamily: "monospace",
          fontSize: 15,
          letterSpacing: 3,
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.28)",
          border: "1px solid rgba(255,255,255,0.18)",
          borderRadius: 999,
          padding: "6px 16px",
        }}
      >
        Placeholder · footage pendente
      </div>
    </AbsoluteFill>
  );
};
