# LivingCities

**The Life-Centric Urbanism Index — powered by living memory.**

Cities are scored not on what they promise, but on what they have actually written down. LivingCities reads a city's own policy documents — master plans, biodiversity strategies, climate programmes — ingests them into a Cognee knowledge graph, and scores how seriously each city designs for life beyond the human. Every verdict carries a verbatim quote. Every quote is traceable to its source.

---

## The Problem

Urban sustainability rankings rely on self-reported surveys, PR metrics, and vague commitments. None of them answer the real question: *does this city's own written record show it actually plans for ecological life?*

LivingCities answers that question from primary sources, in the city's own language.

---

## What We Built

### Cinematic Landing Experience
A scroll-driven, full-screen city transformation built in Next.js + GSAP ScrollTrigger + Lenis. A concrete jungle heals into a living ecosystem in a single scroll gesture. Particle ecology (dust → pollen → leaves → butterflies) responds to scroll progress and cursor position.

### Life-Centric Urbanism Index (LCUI)
An AI-powered scorecard app that:
- Scores cities across **5 pillars × 4 indicators = 20 questions**
- Grounds every score in a verbatim quote from the source document
- Supports **Compare mode** (two cities side by side)
- **Ask** — query the city's memory in natural language, get a cited answer
- **Feedback / Forget** — improve or correct the memory via Cognee Cloud

### Two Cities Scored at Launch
| City | Score | Band |
|---|---|---|
| Geneva | 70 / 100 | Life-Responsive |
| Delhi | 30 / 100 | Ecologically Absent |

---

## The Five Pillars

| # | Pillar | What it measures |
|---|---|---|
| 1 | **Ecological Continuity** | Connected green corridors, blue-green networks, protected zones, dark-sky policy |
| 2 | **Multispecies Infrastructure** | Native species policy, wildlife crossings, green roofs/walls, light pollution |
| 3 | **Ecological Functionality / Regenerative Systems** | Soil health, water cycles, urban farming, renewable integration |
| 4 | **Human-Nature Relationship & Equity** | Access to nature across income levels, biophilic design, education, cultural ties |
| 5 | **Policy Integration & Governance** | Legal standing for nature, biodiversity in planning law, monitoring, cross-dept coordination |

---

## How It Works

```
City PDFs  →  Cognee Cloud (remember)  →  Score 20 indicators (recall)
                                        →  Ask anything (recall)
                                        →  Correct a score (improve / forget)
```

1. **Ingest** — `ingest.py` / `ingest_delhi.py` push each city's PDF documents into Cognee Cloud via `cognee.remember()`
2. **Score** — `scoring.py` poses each of the 20 indicator questions to `cognee.recall()`, maps the answer to `found / partial / not_found`, and computes a weighted pillar score
3. **Serve** — `api.py` (FastAPI) exposes `/score`, `/ask`, `/feedback`, `/forget` endpoints with CORS
4. **Display** — `index.html` fetches live from the API, animates the scores in, and renders the full interactive scorecard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Knowledge memory | **Cognee Cloud** (`remember`, `recall`, `improve`, `forget`) |
| Backend API | **FastAPI** + Uvicorn |
| Landing experience | **Next.js 16** + **GSAP ScrollTrigger** + **Lenis** + **Framer Motion** |
| Particle ecology | Vanilla Canvas rAF (dust → pollen → leaves → butterflies) |
| Scorecard UI | Vanilla HTML/CSS/JS with CSS custom-property palette transitions |
| Fonts | Fraunces (variable), Inter |
| City documents | Primary-source PDFs (Geneva FR/EN, Delhi EN) |

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 20+
- A `.env` file with your Cognee Cloud credentials

```env
COGNEE_SERVICE_URL="https://<your-tenant>.aws.cognee.ai"
COGNEE_API_KEY="<your-key>"
```

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Ingest city documents (run once)

```bash
python ingest.py        # Geneva
python ingest_delhi.py  # Delhi
```

### 3. Start the backend API

```bash
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Serve the scorecard app

```bash
python3 -m http.server 5500
# open http://127.0.0.1:5500/index.html
```

### 5. Run the cinematic landing

```bash
cd experience
npm install
npm run dev -- -p 3010
# open http://127.0.0.1:3010
```

---

## Project Structure

```
livingCities/
├── api.py                  # FastAPI backend (score, ask, feedback, forget)
├── cognee_cloud.py         # Cognee Cloud wrapper (remember/recall/improve/forget)
├── scoring.py              # LCUI scoring engine — 5 pillars × 4 indicators
├── indicators.yaml         # All 20 questions + rubrics (tune here, not in code)
├── ingest.py               # Geneva document ingestion
├── ingest_delhi.py         # Delhi document ingestion
├── index.html              # Scorecard app (single file, zero dependencies)
├── documents/              # Primary source PDFs (Geneva + Delhi)
└── experience/             # Cinematic landing page (Next.js)
    ├── app/                # Next.js App Router
    ├── components/
    │   ├── CityScene.tsx   # Hand-layered SVG city world (1440×810)
    │   ├── Experience.tsx  # Scroll orchestration (Lenis + GSAP)
    │   ├── LaunchButton.tsx# Living button — vine, leaves, butterflies, veil
    │   └── ParticleField.tsx # Canvas ecology (dust → pollen → leaves → butterflies)
    └── next.config.ts
```

---

## Scoring Logic

Each indicator is scored by posing a plain-language question to `cognee.recall()`. The LLM response is mapped to one of three verdicts using a rubric defined in `indicators.yaml`:

| Verdict | Points |
|---|---|
| `found` | 10 |
| `partial` | 5 |
| `not_found` | 0 |

Pillar scores are averages of their four indicators (0–10 → normalised to 0–100). The overall LCUI score is a weighted average across all five pillars.

Score bands:

| Range | Band |
|---|---|
| 80–100 | Ecologically Thriving |
| 60–79 | Life-Responsive |
| 40–59 | Developing Awareness |
| 20–39 | Ecologically Absent |
| 0–19 | Ecologically Blind |

---

## The Vision

A city is a living system. Its policies are its genome. LivingCities makes that genome legible — not through surveys or marketing, but through the city's own words, held in a memory that never forgets and can always be improved.

Every city leaves a written record. We read it.

---

*Built for the Cognee Hackathon 2025.*
