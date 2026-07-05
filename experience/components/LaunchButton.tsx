"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "/app.html";

export default function LaunchButton() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [veil, setVeil] = useState<{ x: number; y: number } | null>(null);

  const launch = (e: React.MouseEvent) => {
    if (veil) return;
    let { clientX: x, clientY: y } = e;
    if (!x && !y) {
      const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
      x = r.left + r.width / 2;
      y = r.top + r.height / 2;
    }
    setVeil({ x, y });
    setTimeout(() => {
      window.location.href = APP_URL;
    }, 1050);
  };

  return (
    <>
      <div ref={wrapRef} className="launch-wrap">

        <svg className="vine-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path
            className="vine-path"
            pathLength={1}
            d="M50,97 C20,97 4,88 4,50 C4,12 24,3 50,3 C76,3 96,12 96,50 C96,88 80,97 50,97"
            fill="none"
            stroke="#7fbf7a"
            strokeWidth="1.6"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>

        <svg className="pointer-events-none absolute -inset-5 h-[calc(100%+40px)] w-[calc(100%+40px)] overflow-visible" aria-hidden="true">
          <g fill="#6fae6a">
            <path className="leafling d1" transform="translate(14 82)" d="M0,0 C-6,-3 -8,-10 -4,-14 C2,-10 3,-4 0,0 Z" />
            <path className="leafling d2" transform="translate(6 30) rotate(-40)" d="M0,0 C-6,-3 -8,-10 -4,-14 C2,-10 3,-4 0,0 Z" />
            <path className="leafling d3" transform="translate(220 12) rotate(30)" d="M0,0 C-6,-3 -8,-10 -4,-14 C2,-10 3,-4 0,0 Z" />
            <path className="leafling d4" transform="translate(232 76) rotate(140)" d="M0,0 C-6,-3 -8,-10 -4,-14 C2,-10 3,-4 0,0 Z" />
          </g>
        </svg>

        {[18, 34, 52, 68, 84].map((left, i) => (
          <span
            key={i}
            className="spore"
            style={{ left: `${left}%`, animationDelay: `${i * 0.33}s` }}
          />
        ))}

        <span className="bfly" style={{ top: -34, left: "12%" }}>
          <svg width="22" height="18" viewBox="0 0 22 18">
            <g className="w">
              <ellipse cx="6" cy="8" rx="6" ry="5" fill="#e8a33d" />
              <ellipse cx="16" cy="8" rx="6" ry="5" fill="#e8a33d" />
            </g>
            <rect x="10" y="3" width="2" height="12" rx="1" fill="#2f3a2c" />
          </svg>
        </span>
        <span className="bfly b2" style={{ top: -20, right: "6%" }}>
          <svg width="18" height="15" viewBox="0 0 22 18">
            <g className="w">
              <ellipse cx="6" cy="8" rx="6" ry="5" fill="#d96f8e" />
              <ellipse cx="16" cy="8" rx="6" ry="5" fill="#d96f8e" />
            </g>
            <rect x="10" y="3" width="2" height="12" rx="1" fill="#2f3a2c" />
          </svg>
        </span>

        <motion.button
          className="launch-btn"
          whileTap={{ scale: 0.96 }}
          onClick={launch}
        >
          <span className="bloom" />
          <span className="label">
            Launch AI
            <svg width="17" height="14" viewBox="0 0 17 14" fill="none" aria-hidden="true">
              <path d="M1 7h14M10 1.5 15.5 7 10 12.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
        </motion.button>
      </div>

      {veil && (
        <motion.div
          className="veil"
          style={{
            ["--vx" as string]: `${veil.x}px`,
            ["--vy" as string]: `${veil.y}px`,
          }}
          initial={{ clipPath: `circle(0% at ${veil.x}px ${veil.y}px)` }}
          animate={{ clipPath: `circle(150% at ${veil.x}px ${veil.y}px)` }}
          transition={{ duration: 1.0, ease: [0.3, 0.6, 0.2, 1] }}
        >
          <div className="flex h-full items-center justify-center">
            <motion.p
              className="font-display text-2xl italic text-[#f4e9c8]"
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45, duration: 0.5 }}
            >
              Entering the living city&hellip;
            </motion.p>
          </div>
        </motion.div>
      )}
    </>
  );
}
