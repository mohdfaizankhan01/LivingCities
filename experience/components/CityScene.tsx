"use client";

/**
 * The city — one hand-layered SVG world, 1440x810.
 * Every class-tagged element is choreographed by the GSAP master
 * timeline in Experience.tsx. Fills reference CSS variables on
 * .stage so the entire palette interpolates with scroll.
 *
 * Layer order (back to front):
 *   sky, sun, clouds, far skyline, mid city (factory, crane, smoke),
 *   canal, front buildings (living walls, green roofs, solar),
 *   street (cars -> people), trees, cracks & tufts, fog, light rays.
 */

function Windows({
  x, y, cols, rows, w = 10, h = 13, gapX = 20, gapY = 26, opacity = 1,
}: {
  x: number; y: number; cols: number; rows: number;
  w?: number; h?: number; gapX?: number; gapY?: number; opacity?: number;
}) {
  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      cells.push(
        <rect
          key={`${r}-${c}`}
          x={x + c * gapX}
          y={y + r * gapY}
          width={w}
          height={h}
          fill="var(--window)"
          opacity={opacity * (((r * 7 + c * 3) % 5 === 0) ? 0.45 : 0.9)}
        />,
      );
    }
  }
  return <g>{cells}</g>;
}

function Tree({ x, base, s = 1, sway = "" }: { x: number; base: number; s?: number; sway?: string }) {
  return (
    <g className="tree" style={{ opacity: 0 }} transform={`translate(${x} ${base}) scale(${s})`}>
      <g className={`sway ${sway}`}>
        <path d="M-3,0 L-2,-34 L2,-34 L3,0 Z" fill="#6b4b33" />
        <circle cx="0" cy="-48" r="20" fill="#4a8354" />
        <circle cx="-14" cy="-38" r="14" fill="#3e7047" />
        <circle cx="14" cy="-38" r="14" fill="#569260" />
        <circle cx="0" cy="-30" r="12" fill="#457a4e" />
      </g>
    </g>
  );
}

function Person({ x, delay, dur }: { x: number; delay: number; dur: number }) {
  return (
    <g
      className="person person-walk"
      style={{ opacity: 0, animationDelay: `${delay}s`, ["--dur" as string]: `${dur}s` }}
      transform={`translate(${x} 0)`}
    >
      <g className="person-bob">
        <circle cx="0" cy="770" r="4.5" fill="#2e4238" />
        <path d="M-3.5,776 L3.5,776 L2.5,796 L-2.5,796 Z" fill="#2e4238" />
      </g>
    </g>
  );
}

export default function CityScene() {
  return (
    <svg
      className="scene-svg absolute inset-0 h-full w-full"
      viewBox="0 0 1440 810"
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="lwall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4d8a58" />
          <stop offset="55%" stopColor="#39714a" />
          <stop offset="100%" stopColor="#2c5c3c" />
        </linearGradient>
        <linearGradient id="warmg" x1="0" y1="0" x2="0.4" y2="1">
          <stop offset="0%" stopColor="#ffd98f" />
          <stop offset="100%" stopColor="#ff9d5c" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="rayg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fff3cf" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#fff3cf" stopOpacity="0" />
        </linearGradient>
        <filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="18" />
        </filter>
        <filter id="fogblur" x="-20%" y="-60%" width="140%" height="220%">
          <feGaussianBlur stdDeviation="26" />
        </filter>
      </defs>

      {/* ================= SKY ================= */}
      <rect className="lyr-sky" width="1440" height="810" fill="var(--sky)" />
      <rect y="380" width="1440" height="330" fill="var(--horizon)" opacity="0.5" />

      {/* sun */}
      <circle className="sun-glow" cx="1105" cy="168" r="95" fill="var(--sun)" opacity="0.18" filter="url(#soft)" />
      <circle cx="1105" cy="168" r="44" fill="var(--sun)" />

      {/* clouds */}
      <g className="cloud-drift" fill="var(--cloud)" opacity="0.85">
        <ellipse cx="180" cy="120" rx="70" ry="20" />
        <ellipse cx="235" cy="106" rx="48" ry="16" />
        <ellipse cx="130" cy="108" rx="38" ry="13" />
      </g>
      <g className="cloud-drift c2" fill="var(--cloud)" opacity="0.65">
        <ellipse cx="640" cy="72" rx="85" ry="22" />
        <ellipse cx="705" cy="58" rx="52" ry="15" />
      </g>
      <g className="cloud-drift c3" fill="var(--cloud)" opacity="0.5">
        <ellipse cx="1010" cy="230" rx="60" ry="16" />
        <ellipse cx="1058" cy="219" rx="36" ry="11" />
      </g>

      {/* birds — gated by scroll, loop across sky */}
      <g className="flock" style={{ opacity: 0 }}>
        <g className="flock-fly" stroke="#243830" strokeWidth="2.4" strokeLinecap="round" fill="none">
          <path className="wing" d="M0,200 Q6,194 12,200 M12,200 Q18,194 24,200" />
          <path className="wing" d="M38,214 Q44,208 50,214 M50,214 Q56,208 62,214" style={{ animationDelay: "-0.2s" }} />
          <path className="wing" d="M20,228 Q26,222 32,228 M32,228 Q38,222 44,228" style={{ animationDelay: "-0.35s" }} />
        </g>
        <g className="flock-fly f2" stroke="#243830" strokeWidth="2" strokeLinecap="round" fill="none">
          <path className="wing" d="M0,150 Q5,145 10,150 M10,150 Q15,145 20,150" style={{ animationDelay: "-0.1s" }} />
          <path className="wing" d="M28,160 Q33,155 38,160 M38,160 Q43,155 48,160" style={{ animationDelay: "-0.3s" }} />
        </g>
      </g>

      {/* ================= FAR SKYLINE ================= */}
      <g data-depth="8">
        <path
          fill="var(--far)"
          d="M0,600 L0,520 L60,520 L60,478 L110,478 L110,520 L170,520 L170,455
             L215,455 L215,500 L275,500 L275,468 L330,468 L330,530 L400,530 L400,490
             L450,490 L450,540 L520,540 L520,470 L560,470 L560,430 L600,430 L600,540
             L680,540 L680,500 L740,500 L740,455 L790,455 L790,520 L860,520 L860,480
             L915,480 L915,532 L985,532 L985,462 L1030,462 L1030,505 L1095,505
             L1095,472 L1150,472 L1150,530 L1225,530 L1225,488 L1280,488 L1280,540
             L1350,540 L1350,502 L1440,502 L1440,600 Z"
        />
      </g>

      {/* ================= MID CITY ================= */}
      <g data-depth="16">
        {/* mid blocks */}
        <g fill="var(--mid)">
          <rect x="470" y="430" width="80" height="230" />
          <rect x="560" y="380" width="65" height="280" />
          <rect x="880" y="410" width="75" height="250" />
          <rect x="962" y="452" width="58" height="208" />
        </g>
        <Windows x={480} y={445} cols={3} rows={7} gapX={26} gapY={30} opacity={0.4} />
        <Windows x={572} y={396} cols={2} rows={8} gapX={28} gapY={32} opacity={0.4} />
        <Windows x={892} y={426} cols={3} rows={7} gapX={24} gapY={31} opacity={0.4} />

        {/* factory */}
        <g>
          <rect x="700" y="580" width="150" height="80" fill="var(--mid)" />
          <path d="M700,580 L737,556 L737,580 L774,556 L774,580 L811,556 L811,580 Z" fill="var(--mid)" />
          <rect x="726" y="498" width="15" height="82" fill="var(--front)" />
          <rect x="790" y="482" width="15" height="98" fill="var(--front)" />
          {/* smoke */}
          <g className="smoke-g" fill="#9aa3ab">
            <circle className="smoke-p" cx="733" cy="492" r="11" />
            <circle className="smoke-p p2" cx="733" cy="492" r="9" />
            <circle className="smoke-p p3" cx="733" cy="492" r="12" />
            <circle className="smoke-p p2" cx="797" cy="476" r="12" />
            <circle className="smoke-p p3" cx="797" cy="476" r="9" />
            <circle className="smoke-p" cx="797" cy="476" r="11" />
          </g>
        </g>

        {/* construction crane */}
        <g className="crane" stroke="var(--front)" strokeWidth="5" fill="none">
          <path d="M648,660 L648,404" />
          <path d="M560,418 L775,418" strokeWidth="4" />
          <path d="M648,404 L648,388 L700,418 M648,388 L596,418" strokeWidth="3" />
          <path d="M736,418 L736,470" strokeWidth="2" />
          <rect x="729" y="470" width="14" height="12" fill="var(--front)" stroke="none" />
          <rect x="574" y="410" width="30" height="14" fill="var(--front)" stroke="none" />
        </g>
      </g>

      {/* ================= CANAL ================= */}
      <g>
        <rect x="0" y="644" width="470" height="60" fill="var(--river)" />
        <path className="ripple" d="M20,662 q30,-5 60,0 t60,0 t60,0 t60,0" stroke="#ffffff" strokeOpacity="0.13" strokeWidth="2.5" fill="none" />
        <path className="ripple r2" d="M50,682 q30,-5 60,0 t60,0 t60,0 t60,0" stroke="#ffffff" strokeOpacity="0.1" strokeWidth="2" fill="none" />
        {/* clean-water sparkles */}
        <g className="sparkle" fill="#eafaff" style={{ opacity: 0 }}>
          <circle cx="90" cy="668" r="2.2" />
          <circle cx="210" cy="688" r="1.8" />
          <circle cx="315" cy="672" r="2.4" />
          <circle cx="410" cy="690" r="1.6" />
        </g>
        <rect x="0" y="640" width="470" height="6" fill="var(--front2)" />
      </g>

      {/* ================= FRONT BUILDINGS ================= */}
      <g data-depth="26">
        {/* B1 */}
        <g>
          <rect x="60" y="318" width="185" height="326" fill="var(--front)" />
          <Windows x={78} y={338} cols={6} rows={9} gapX={26} gapY={31} />
          {/* living wall grows over the facade */}
          <rect className="lwall" x="60" y="318" width="185" height="326" fill="url(#lwall)" style={{ opacity: 0 }} rx="4" />
          {/* moss patches */}
          <g className="moss" fill="#4b7d4f" style={{ opacity: 0 }}>
            <ellipse cx="70" cy="630" rx="26" ry="10" />
            <ellipse cx="240" cy="480" rx="12" ry="26" />
          </g>
          {/* solar array on roof */}
          <g className="solar" style={{ opacity: 0 }}>
            <rect x="76" y="300" width="38" height="14" fill="#2c4f6b" transform="skewX(-16)" />
            <rect x="126" y="300" width="38" height="14" fill="#325a7a" transform="skewX(-16)" />
            <rect x="176" y="300" width="38" height="14" fill="#2c4f6b" transform="skewX(-16)" />
          </g>
          {/* vine climbing the corner */}
          <path
            className="vine"
            pathLength={1}
            d="M62,642 C40,560 96,520 66,452 C48,408 92,380 74,330"
            stroke="#3f7f52" strokeWidth="4" strokeLinecap="round" fill="none"
            strokeDasharray="1" strokeDashoffset="1"
          />
        </g>

        {/* B2 */}
        <g>
          <rect x="292" y="402" width="150" height="242" fill="var(--front2)" />
          <Windows x={308} y={420} cols={5} rows={7} gapX={26} gapY={30} />
          <rect className="groof" x="292" y="392" width="150" height="12" rx="5" fill="#4d8a58" style={{ opacity: 0, transform: "scaleY(0)", transformOrigin: "50% 100%" }} />
        </g>

        {/* B3 */}
        <g>
          <rect x="948" y="362" width="168" height="282" fill="var(--front2)" />
          <Windows x={964} y={382} cols={6} rows={8} gapX={25} gapY={31} />
          <rect className="groof" x="948" y="352" width="168" height="12" rx="5" fill="#4d8a58" style={{ opacity: 0, transform: "scaleY(0)", transformOrigin: "50% 100%" }} />
          <g className="moss" fill="#4b7d4f" style={{ opacity: 0 }}>
            <ellipse cx="952" cy="600" rx="10" ry="24" />
          </g>
        </g>

        {/* B4 */}
        <g>
          <rect x="1198" y="258" width="182" height="386" fill="var(--front)" />
          <Windows x={1214} y={278} cols={6} rows={11} gapX={27} gapY={31} />
          <rect className="lwall" x="1198" y="258" width="182" height="386" fill="url(#lwall)" style={{ opacity: 0 }} rx="4" />
          <g className="solar" style={{ opacity: 0 }}>
            <rect x="1290" y="240" width="38" height="14" fill="#2c4f6b" transform="skewX(-16)" />
            <rect x="1340" y="240" width="38" height="14" fill="#325a7a" transform="skewX(-16)" />
          </g>
          <path
            className="vine"
            pathLength={1}
            d="M1382,642 C1400,560 1352,516 1378,448 C1394,404 1356,368 1372,300"
            stroke="#3f7f52" strokeWidth="4" strokeLinecap="round" fill="none"
            strokeDasharray="1" strokeDashoffset="1"
          />
        </g>
      </g>

      {/* ================= STREET ================= */}
      <g>
        <rect x="0" y="644" width="1440" height="166" fill="var(--ground)" />
        {/* road */}
        <rect x="0" y="700" width="1440" height="66" fill="var(--road)" />
        {/* lane dashes */}
        <g className="lanes" fill="#c9cdd1" opacity="0.5">
          {Array.from({ length: 15 }, (_, i) => (
            <rect key={i} x={i * 100 + 12} y="731" width="42" height="4" rx="2" />
          ))}
        </g>
        {/* median that becomes a park strip */}
        <rect className="median" x="0" y="726" width="1440" height="14" fill="var(--grass)" style={{ opacity: 0, transform: "scaleY(0)", transformOrigin: "50% 100%" }} />

        {/* cars */}
        <g className="car car-l" style={{ ["--dur" as string]: "16s" }}>
          <rect x="0" y="708" width="46" height="15" rx="6" fill="#3a4046" />
          <rect x="8" y="702" width="24" height="10" rx="4" fill="#4a525a" />
        </g>
        <g className="car car-l" style={{ ["--dur" as string]: "21s", animationDelay: "-8s" }}>
          <rect x="0" y="708" width="52" height="15" rx="6" fill="#565f68" />
          <rect x="10" y="702" width="28" height="10" rx="4" fill="#666f79" />
        </g>
        <g className="car car-r" style={{ ["--dur" as string]: "14s" }}>
          <rect x="0" y="744" width="46" height="15" rx="6" fill="#2e3439" />
          <rect x="8" y="738" width="24" height="10" rx="4" fill="#3c434a" />
        </g>
        <g className="car car-r" style={{ ["--dur" as string]: "19s", animationDelay: "-11s" }}>
          <rect x="0" y="744" width="40" height="15" rx="6" fill="#4d565f" />
          <rect x="7" y="738" width="22" height="10" rx="4" fill="#5b656f" />
        </g>

        {/* people, when the street calms */}
        <Person x={0} delay={0} dur={58} />
        <Person x={0} delay={-20} dur={70} />
        <Person x={0} delay={-42} dur={64} />
      </g>

      {/* ================= TREES ================= */}
      <g>
        {/* back sidewalk row */}
        <Tree x={510} base={700} s={0.85} />
        <Tree x={618} base={700} s={0.95} sway="s2" />
        <Tree x={868} base={700} s={0.8} sway="s3" />
        <Tree x={1132} base={700} s={0.98} />
        <Tree x={278} base={700} s={0.9} sway="s2" />
        {/* foreground giants, partially cropped */}
        <Tree x={64} base={810} s={2.3} sway="s3" />
        <Tree x={1382} base={810} s={2.6} sway="s2" />
        <Tree x={1240} base={806} s={1.5} />
      </g>

      {/* ================= CRACKS & TUFTS ================= */}
      <g>
        <path
          className="crack"
          pathLength={1}
          d="M330,806 L352,788 L348,776 L372,764 L392,752"
          stroke="#272c31" strokeWidth="2.5" fill="none" strokeLinecap="round"
          strokeDasharray="1" strokeDashoffset="1"
        />
        <path
          className="crack"
          pathLength={1}
          d="M980,808 L964,790 L972,778 L950,766"
          stroke="#272c31" strokeWidth="2.5" fill="none" strokeLinecap="round"
          strokeDasharray="1" strokeDashoffset="1"
        />
        {[ [352, 790], [372, 766], [966, 792], [954, 768], [392, 754] ].map(([x, y], i) => (
          <g key={i} className="tuft" style={{ opacity: 0, transform: "scale(0)", transformOrigin: "50% 100%" }} transform={`translate(${x} ${y})`}>
            <path d="M0,0 C-2,-7 -5,-9 -6,-14 M0,0 C0,-9 1,-11 0,-17 M0,0 C2,-7 5,-9 7,-13"
              stroke="#5e9a54" strokeWidth="2" fill="none" strokeLinecap="round" />
          </g>
        ))}
      </g>

      {/* ================= ATMOSPHERE ================= */}
      {/* fog banks */}
      <rect className="fog" x="-60" y="470" width="1560" height="180" fill="#c3c9cf" opacity="0.5" filter="url(#fogblur)" />
      <rect className="fog" x="-60" y="270" width="1560" height="110" fill="#ced3d8" opacity="0.32" filter="url(#fogblur)" />

      {/* light rays, at the end */}
      <g className="rays" style={{ opacity: 0 }}>
        <rect x="1010" y="90" width="60" height="560" fill="url(#rayg)" transform="rotate(24 1040 90)" />
        <rect x="1130" y="70" width="42" height="520" fill="url(#rayg)" transform="rotate(24 1150 70)" opacity="0.7" />
        <rect x="890" y="120" width="34" height="480" fill="url(#rayg)" transform="rotate(24 907 120)" opacity="0.5" />
      </g>

      {/* warm sunlight wash */}
      <rect className="warm" width="1440" height="810" fill="url(#warmg)" style={{ opacity: 0, mixBlendMode: "soft-light" }} />
    </svg>
  );
}
