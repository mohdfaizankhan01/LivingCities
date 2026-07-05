"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import CityScene from "./CityScene";
import ParticleField from "./ParticleField";
import LaunchButton from "./LaunchButton";

gsap.registerPlugin(ScrollTrigger);

/**
 * One single scroll heals the city — the whole transformation plays
 * across one viewport of scrolling (a ~150vh track). A scrubbed GSAP
 * timeline (0-10) drives it:
 *
 *  0.0  hero fades, palette begins to soften
 *  2.0  concrete cracks, first grass appears
 *  3.0  smoke thins, moss spreads
 *  4.2  vines climb, fog starts to lift
 *  5.2  trees rise, green roofs unroll, the median becomes a park
 *  6.2  solar panels catch light, traffic dissolves, warmth arrives
 *  7.6  people walk, water clears
 *  8.2  birds return, light rays break through
 *  8.6  the finale: one living city, one button
 */

const END_PALETTE: Record<string, string> = {
  "--sky": "#9fd8f2",
  "--horizon": "#cfeadf",
  "--cloud": "#f4f9fb",
  "--sun": "#ffd27a",
  "--far": "#7ca98b",
  "--mid": "#93a98f",
  "--front": "#6d8071",
  "--front2": "#5f7365",
  "--window": "#ffd98f",
  "--ground": "#4e6b4c",
  "--road": "#4c5b50",
  "--river": "#57b7c9",
  "--grass": "#5e9a54",
};

const MID_PALETTE: Record<string, string> = {
  "--sky": "#b2c3c9",
  "--horizon": "#c3cdc9",
  "--window": "#c8cdc8",
  "--river": "#5b7278",
};

export default function Experience() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef(0);
  const [reduced, setReduced] = useState(false);
  const [ready, setReady] = useState(false);

  useLayoutEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const stage = stageRef.current!;

    if (prefersReduced) {
      // The world arrives already healed — no scrub, no particles.
      gsap.set(stage, { ...END_PALETTE });
      gsap.set(".tree", { scale: 1, opacity: 1, transformOrigin: "50% 100%" });
      gsap.set(".groof", { scaleY: 1, opacity: 1 });
      gsap.set(".median", { scaleY: 1, opacity: 1 });
      gsap.set(".tuft", { scale: 1, opacity: 1 });
      gsap.set(".lwall", { opacity: 0.92 });
      gsap.set(".moss", { opacity: 0.9 });
      gsap.set(".solar, .flock, .sparkle, .person", { opacity: 1 });
      gsap.set(".vine, .crack", { strokeDashoffset: 0 });
      gsap.set(".smoke-g, .fog, .car", { opacity: 0 });
      gsap.set(".rays", { opacity: 0.4 });
      gsap.set(".warm", { opacity: 0.3 });
      gsap.set(".finale", { opacity: 1, pointerEvents: "auto" });
      progressRef.current = 1;
      return;
    }

    const lenis = new Lenis({ lerp: 0.1 });
    (window as unknown as Record<string, unknown>).__lenis = lenis;
    lenis.on("scroll", ScrollTrigger.update);
    const rafCb = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(rafCb);
    gsap.ticker.lagSmoothing(0);

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: {
          trigger: wrapRef.current,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.8,
          onUpdate: (self) => {
            progressRef.current = self.progress;
          },
        },
      });

      /* ---- hero departs ---- */
      tl.to(".hero-copy", { opacity: 0, y: -70, duration: 1 }, 0);
      tl.to(".scroll-hint", { opacity: 0, duration: 0.5 }, 0);

      /* ---- palette: cold -> thawing -> alive ---- */
      tl.to(stage, { ...MID_PALETTE, duration: 3.4 }, 0.4);
      tl.to(stage, { ...END_PALETTE, duration: 4.8 }, 4.0);

      /* ---- act I: the first cracks of life ---- */
      tl.to(".crack", { strokeDashoffset: 0, duration: 1.4, stagger: 0.35 }, 2.0);
      tl.fromTo(".tuft",
        { scale: 0, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.8, stagger: 0.18, ease: "back.out(2.2)", transformOrigin: "50% 100%" },
        2.7);
      tl.to(".smoke-g", { opacity: 0, duration: 1.8 }, 3.0);
      tl.to(".moss", { opacity: 0.9, duration: 1.6, stagger: 0.25 }, 3.2);

      /* ---- act II: the climb ---- */
      tl.to(".vine", { strokeDashoffset: 0, duration: 2.2, stagger: 0.5 }, 4.2);
      tl.to(".fog", { opacity: 0, duration: 2.4, stagger: 0.3 }, 4.5);
      tl.to(".lwall", { opacity: 0.92, duration: 2.0, stagger: 0.4 }, 5.0);
      tl.fromTo(".tree",
        { scale: 0, opacity: 0 },
        { scale: 1, opacity: 1, duration: 1.6, ease: "back.out(1.3)", transformOrigin: "50% 100%",
          stagger: { each: 0.22, from: "random" } },
        5.2);
      tl.fromTo(".groof",
        { scaleY: 0, opacity: 0 },
        { scaleY: 1, opacity: 1, duration: 1.2, stagger: 0.3, transformOrigin: "50% 100%" },
        5.5);
      tl.fromTo(".median",
        { scaleY: 0, opacity: 0 },
        { scaleY: 1, opacity: 1, duration: 1.0, transformOrigin: "50% 100%" },
        5.9);

      /* ---- act III: light and quiet ---- */
      tl.to(".solar", { opacity: 1, duration: 1.2, stagger: 0.25 }, 6.2);
      tl.to(".car", { opacity: 0, duration: 1.6, stagger: 0.2 }, 6.1);
      tl.to(".lanes", { opacity: 0.15, duration: 1.5 }, 6.2);
      tl.to(".crane", { opacity: 0, duration: 1.6 }, 6.4);
      tl.to(".sun-glow", { opacity: 0.85, duration: 2.4 }, 6.5);
      tl.to(".warm", { opacity: 0.3, duration: 2.8 }, 6.6);

      /* ---- act IV: life returns ---- */
      tl.to(".person", { opacity: 1, duration: 1.1, stagger: 0.3 }, 7.6);
      tl.to(".sparkle", { opacity: 0.9, duration: 1.0 }, 7.9);
      tl.to(".flock", { opacity: 1, duration: 1.0 }, 8.2);
      tl.to(".rays", { opacity: 0.45, duration: 1.4 }, 8.3);

      /* ---- gentle camera ---- */
      tl.fromTo(".scene-svg", { scale: 1.07, yPercent: 1.6 }, { scale: 1, yPercent: 0, duration: 10, ease: "power1.out" }, 0);

      /* ---- finale ---- */
      tl.fromTo(".finale", { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 1.2, ease: "power2.out" }, 8.6);
      tl.set(".finale", { pointerEvents: "auto" }, 8.9);

      /* ---- pointer parallax on scene layers ---- */
      const layers = gsap.utils.toArray<SVGGElement>("[data-depth]");
      const setters = layers.map((l) => ({
        x: gsap.quickTo(l, "x", { duration: 0.9, ease: "power2.out" }),
        y: gsap.quickTo(l, "y", { duration: 0.9, ease: "power2.out" }),
        d: parseFloat(l.dataset.depth ?? "10"),
      }));
      const onPointer = (e: PointerEvent) => {
        const nx = e.clientX / window.innerWidth - 0.5;
        const ny = e.clientY / window.innerHeight - 0.5;
        for (const s of setters) {
          s.x(-nx * s.d);
          s.y(-ny * s.d * 0.5);
        }
      };
      window.addEventListener("pointermove", onPointer, { passive: true });
      return () => window.removeEventListener("pointermove", onPointer);
    }, wrapRef);

    return () => {
      ctx.revert();
      gsap.ticker.remove(rafCb);
      lenis.destroy();
    };
  }, [ready]);

  return (
    <main>
      <div ref={wrapRef} className="relative h-[150vh]">
        <div ref={stageRef} className="stage sticky top-0 h-screen overflow-hidden">
          <CityScene />
          <ParticleField progressRef={progressRef} disabled={reduced} />

          {/* logo — the only permanent chrome */}
          <div className="absolute left-8 top-7 z-40 select-none md:left-12">
            <span className="font-display text-xl text-[#f2f5ef]/95">
              Living<em className="italic text-[#f4e9c8]">Cities</em>
            </span>
          </div>

          {/* hero — entrance is pure CSS; GSAP owns the parent */}
          <div className="hero-copy absolute inset-0 z-30 flex flex-col items-start justify-center px-8 md:px-[8vw]">
            <h1 className="hero-headline rise-in r1 max-w-[13ch] text-[#f2f5ef]">
              Designing cities that let <em>life thrive</em>.
            </h1>
            <p className="rise-in r2 mt-7 max-w-[46ch] text-base text-[#e9eef0]/70 md:text-lg">
              Our AI transforms urban planning into a living, regenerative
              system where people, biodiversity, and infrastructure evolve
              together.
            </p>
          </div>

          {/* scroll hint */}
          <div className="scroll-hint absolute bottom-8 left-1/2 z-30 flex -translate-x-1/2 flex-col items-center gap-3">
            <div className="fade-in-late flex flex-col items-center gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#e9eef0]/55">
                Scroll to heal the city
              </span>
              <span className="scroll-hint-line" />
            </div>
          </div>

          {/* finale — one city, one button */}
          <div className="finale pointer-events-none absolute inset-x-0 bottom-[14vh] z-40 flex flex-col items-center gap-8 text-center" style={{ opacity: 0 }}>
            <p className="font-display max-w-[26ch] text-2xl font-light italic text-[#10241a] md:text-4xl" style={{ textShadow: "0 1px 24px rgba(245,250,246,.55)" }}>
              You just watched a city come back to life.
            </p>
            <LaunchButton />
          </div>

          <div className="grain" />
        </div>
      </div>
    </main>
  );
}
