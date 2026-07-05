# LivingCities — Demo Video Script

> **Narrator:** Safir (sole speaker for the entire video)
> **Hard limit:** 3:00 — this script runs ~2:45 at a calm 150 wpm (≈ 410 spoken words)
> **Team:** noName · **Hackathon:** The Hangover Part AI
> **Live demo:** https://livingcities-app.netlify.app

**Covers the four required submission points, in this order:**
1. **About the project** — Scene 1
2. **Demo** — Scenes 2–6 (the core of the video)
3. **Tech stack & architecture** — Scene 7
4. **Learning & growth** *(optional)* — Scene 8

**Reading key:** **[SCREEN]** = what to show / do · **[SAFIR]** = exact words to say · **(pause)** = short beat for the visual to land. Only Safir speaks — no second voice anywhere.

---

## 1 · ABOUT THE PROJECT  `0:00 – 0:32`

**[SCREEN]** Open on the landing hero — the grey concrete city, still. Hold it for two seconds. Don't scroll yet.

**[SAFIR]**
> Cities today are planned for cars and concrete — and for almost nothing else alive.
> (pause)
> I'm Safir, from team noName, and this is LivingCities. We measure how well a city is designed for life beyond the human — not from surveys or press releases, but from the city's *own* policy documents. And every score is backed by a real quote, traceable to its source.

---

## 2 · DEMO — The Living Transformation  `0:32 – 0:52`

**[SCREEN]** Scroll the landing page slowly. The grey city heals in one continuous motion — grass, vines, trees, warm sky, butterflies, blue water. Reach the **Launch AI** button; hover so the vine draws itself, then click. The green veil carries you into the app.

**[SAFIR]**
> It begins as an experience. Watch a grey city heal into a living one as you scroll — every element mapped to a real planning decision a city can make.
> (pause)
> And then you launch the index behind it.

---

## 3 · DEMO — Scores From the Evidence  `0:52 – 1:22`

**[SCREEN]** Geneva's scorecard animates in to **70 / 100**, "Life-Responsive." Expand **Ecological Continuity** to reveal indicators and a verbatim French quote. Then click the **Delhi** tab — the score re-counts down to **30 / 100**, "Ecologically Absent."

**[SAFIR]**
> Here's Geneva — seventy out of a hundred. Life-Responsive. Five pillars, twenty indicators, each one grounded in a verbatim quote from Geneva's own documents, in the original French.
> (pause)
> Delhi scores thirty — Ecologically Absent. Same twenty indicators, the same standard, applied honestly — a measure a city can't spin.

---

## 4 · DEMO — Compare  `1:22 – 1:34`

**[SCREEN]** Click **Compare**. Both cities render side by side, bars animating, Geneva leading pillar by pillar.

**[SAFIR]**
> Side by side, the gap stops being a number and becomes a diagnosis — exactly which pillars a city is failing, and where the work begins.

---

## 5 · DEMO — Ask the City's Memory  `1:34 – 2:04`  *(the highlight)*

**[SCREEN]** Scroll to **Ask the city's memory**. Type *"Does Geneva protect biodiversity corridors?"* and click **Ask**. Wait for the grounded answer, verbatim quote, translation, and source file to render.

**[SAFIR]**
> But the real power is that these documents become a living memory you can *question*. I'll ask Geneva directly — does it protect biodiversity corridors?
> (pause — answer appears)
> And there it is: a grounded answer pulled straight from the source, with the original quote, an English translation, and the exact file it came from. No hallucination — only what the city actually wrote.

---

## 6 · DEMO — Living Memory  `2:04 – 2:14`

**[SCREEN]** Scroll to the **Live memory demo** — Expert feedback and Update memory panels. Gesture to them; optionally submit one correction and let the score re-animate.

**[SAFIR]**
> And it's alive. An expert can correct the memory, or forget a repealed policy — and the score updates on the spot.

---

## 7 · TECH STACK & ARCHITECTURE  `2:14 – 2:44`

**[SCREEN]** Cut to a simple architecture card / the README diagram: **City PDFs → Cognee (remember) → recall → ask / improve / forget**, with **Next.js + Netlify** on the front and **FastAPI + Hugging Face** on the back.

**[SAFIR]**
> Under the hood, the intelligence runs on Cognee. We *remember* each city's documents into a knowledge graph, *recall* evidence for every indicator, and *improve* that memory with expert feedback.
> (pause)
> The cinematic front end is Next.js with GSAP, on Netlify. The scoring API is FastAPI in a Docker container on Hugging Face, talking to Cognee Cloud — scores load instantly from cached snapshots, while Ask hits the live backend.

---

## 8 · LEARNING & GROWTH  `2:44 – 3:00`  *(optional)*

**[SCREEN]** Return to the healed living city — the final landing frame or the LivingCities logo.

**[SAFIR]**
> What we learned: grounding a model in a real memory changes everything — every answer became traceable and honest. The hardest part was teaching the AI to say "I don't know" when the documents are silent — and that restraint is exactly what makes the index trustworthy.
> (pause)
> Every city leaves a written record. LivingCities reads it. Thank you.

---

## Appendix · Recording Checklist

- [ ] **Wake the backend ~1 minute before recording:** open `https://faizkh7786-livingcities-api.hf.space/health`. The free Space sleeps after ~48h idle, and a cold Ask can take ~30s.
- [ ] Pre-type the Ask question, or accept one clean typing beat, so the take stays under time.
- [ ] Record at 1440p+, clean browser profile, bookmarks bar hidden.
- [ ] Take the Scene 2 scroll **slowly** — the transformation is the wow moment.
- [ ] Watch the clock: total must be **≤ 3:00**. If over, trim Scene 6 first (mention feedback verbally in Scene 5).
- [ ] **One voice only — Safir narrates start to finish.**

## Appendix · Timing Map (for quick checks)

| # | Section | Requirement point | Ends at |
|---|---|---|---|
| 1 | About the project | About | 0:32 |
| 2–6 | Product walkthrough | Demo | 2:14 |
| 7 | Cognee + Next.js + FastAPI + hosting | Tech stack & architecture | 2:44 |
| 8 | Grounding, honesty, the hard part | Learning & growth (optional) | 3:00 |

## Appendix · One-Line Pitch (title card / caption)

> **LivingCities** — the Life-Centric Urbanism Index. We score cities on ecological integrity from their own policy documents, powered by living memory.
