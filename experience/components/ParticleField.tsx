"use client";

import { useEffect, useRef, type RefObject } from "react";

/**
 * One canvas, one rAF loop, an entire ecology.
 * The mix of particles is driven by scroll progress (progressRef):
 *   p ~ 0   : industrial dust, slow and grey
 *   p > 0.45: pollen and drifting leaves fade in as dust settles
 *   p > 0.55: butterflies arrive and gently follow the cursor
 * Everything is alpha-weighted, never popped.
 */

type Dust = { x: number; y: number; r: number; vx: number; vy: number; a: number };
type Leaf = { x: number; y: number; s: number; vx: number; vy: number; rot: number; vr: number; hue: number };
type Butterfly = { x: number; y: number; vx: number; vy: number; t: number; hue: string; s: number };

const smooth = (p: number, a: number, b: number) => {
  const t = Math.min(1, Math.max(0, (p - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export default function ParticleField({
  progressRef,
  disabled,
}: {
  progressRef: RefObject<number>;
  disabled: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (disabled) return;
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    let W = 0;
    let H = 0;
    let raf = 0;
    let running = true;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      W = canvas.clientWidth;
      H = canvas.clientHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const rand = (a: number, b: number) => a + Math.random() * (b - a);

    const dust: Dust[] = Array.from({ length: 55 }, () => ({
      x: rand(0, 1600), y: rand(0, 900), r: rand(0.6, 2.2),
      vx: rand(-0.12, 0.12), vy: rand(-0.06, 0.1), a: rand(0.04, 0.14),
    }));

    const pollen: Dust[] = Array.from({ length: 45 }, () => ({
      x: rand(0, 1600), y: rand(0, 900), r: rand(1, 2.6),
      vx: rand(-0.18, 0.24), vy: rand(-0.22, -0.05), a: rand(0.25, 0.6),
    }));

    const leaves: Leaf[] = Array.from({ length: 11 }, () => ({
      x: rand(0, 1600), y: rand(-200, 700), s: rand(4, 8),
      vx: rand(0.15, 0.5), vy: rand(0.25, 0.6),
      rot: rand(0, Math.PI * 2), vr: rand(-0.02, 0.02), hue: rand(88, 128),
    }));

    const bflies: Butterfly[] = Array.from({ length: 4 }, (_, i) => ({
      x: rand(200, 1200), y: rand(200, 600),
      vx: 0, vy: 0, t: rand(0, 100),
      hue: ["#e8a33d", "#d96f8e", "#7cc4e8", "#c9de6a"][i], s: rand(0.8, 1.25),
    }));

    const cursor = { x: -9999, y: -9999 };
    const onMove = (e: PointerEvent) => {
      cursor.x = e.clientX;
      cursor.y = e.clientY;
    };
    window.addEventListener("pointermove", onMove, { passive: true });

    const onVis = () => { running = !document.hidden; if (running) raf = requestAnimationFrame(tick); };
    document.addEventListener("visibilitychange", onVis);

    const drawButterfly = (b: Butterfly, alpha: number) => {
      const flap = 0.2 + Math.abs(Math.sin(b.t * 0.28)) * 0.8; // 0.2..1 wing spread, never negative
      ctx.save();
      ctx.translate(b.x, b.y);
      ctx.rotate(Math.atan2(b.vy, b.vx) * 0.25);
      ctx.scale(b.s, b.s);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = b.hue;
      // wings
      ctx.beginPath();
      ctx.ellipse(-5 * flap, -3, 6 * flap, 4.4, -0.5, 0, Math.PI * 2);
      ctx.ellipse(5 * flap, -3, 6 * flap, 4.4, 0.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(-4 * flap, 3, 4.4 * flap, 3.2, -0.9, 0, Math.PI * 2);
      ctx.ellipse(4 * flap, 3, 4.4 * flap, 3.2, 0.9, 0, Math.PI * 2);
      ctx.fill();
      // body
      ctx.fillStyle = "#2f3a2c";
      ctx.beginPath();
      ctx.ellipse(0, 0, 1.4, 5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    };

    const tick = () => {
      if (!running) return;
      const p = progressRef.current ?? 0;
      ctx.clearRect(0, 0, W, H);

      const dustA = 1 - smooth(p, 0.25, 0.6);
      const lifeA = smooth(p, 0.45, 0.75);
      const bflyA = smooth(p, 0.55, 0.8);

      // dust
      if (dustA > 0.01) {
        ctx.fillStyle = "#cfd6da";
        for (const d of dust) {
          d.x += d.vx; d.y += d.vy;
          if (d.x < -10) d.x = W + 10; if (d.x > W + 10) d.x = -10;
          if (d.y < -10) d.y = H + 10; if (d.y > H + 10) d.y = -10;
          ctx.globalAlpha = d.a * dustA;
          ctx.beginPath();
          ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // pollen — warm motes rising
      if (lifeA > 0.01) {
        for (const m of pollen) {
          m.x += m.vx + Math.sin((m.y + m.x) * 0.01) * 0.1;
          m.y += m.vy;
          if (m.y < -10) { m.y = H + 10; m.x = Math.random() * W; }
          if (m.x < -10) m.x = W + 10; if (m.x > W + 10) m.x = -10;
          ctx.globalAlpha = m.a * lifeA * 0.55;
          ctx.fillStyle = "#ffeaa8";
          ctx.beginPath();
          ctx.arc(m.x, m.y, m.r * 2.4, 0, Math.PI * 2);
          ctx.fill();
          ctx.globalAlpha = m.a * lifeA;
          ctx.fillStyle = "#fff3c9";
          ctx.beginPath();
          ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2);
          ctx.fill();
        }

        // leaves
        for (const l of leaves) {
          l.x += l.vx + Math.sin(l.rot * 2) * 0.3;
          l.y += l.vy;
          l.rot += l.vr;
          if (l.y > H + 20) { l.y = -20; l.x = Math.random() * W; }
          if (l.x > W + 20) l.x = -20;
          ctx.save();
          ctx.translate(l.x, l.y);
          ctx.rotate(l.rot);
          ctx.globalAlpha = 0.75 * lifeA;
          ctx.fillStyle = `hsl(${l.hue} 38% 46%)`;
          ctx.beginPath();
          ctx.ellipse(0, 0, l.s, l.s * 0.45, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }
      }

      // butterflies — wander plus gentle cursor curiosity
      if (bflyA > 0.01) {
        for (const b of bflies) {
          b.t += 1;
          let ax = Math.cos(b.t * 0.017) * 0.028;
          let ay = Math.sin(b.t * 0.023) * 0.024;
          const dx = cursor.x - b.x;
          const dy = cursor.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 320 && dist > 40) {
            ax += (dx / dist) * 0.05;
            ay += (dy / dist) * 0.05;
          } else if (dist <= 40) {
            ax -= (dx / dist) * 0.09; // too close — flutter away
            ay -= (dy / dist) * 0.09;
          }
          b.vx = (b.vx + ax) * 0.985;
          b.vy = (b.vy + ay + Math.sin(b.t * 0.4) * 0.012) * 0.985;
          b.x += b.vx;
          b.y += b.vy;
          if (b.x < 30) b.vx += 0.05; if (b.x > W - 30) b.vx -= 0.05;
          if (b.y < 60) b.vy += 0.05; if (b.y > H - 80) b.vy -= 0.05;
          drawButterfly(b, bflyA * 0.95);
        }
      }

      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [disabled, progressRef]);

  if (disabled) return null;
  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 z-20 h-full w-full"
      aria-hidden="true"
    />
  );
}
