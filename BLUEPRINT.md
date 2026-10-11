# Kavach — Blueprint & Handoff Document

> **If you are a new Claude session, a new account, or a teammate reading this cold:**
> This file is the single source of truth for what Kavach is and how to build it.
> Read this file top to bottom before writing any code. The "Status" section at the
> bottom tells you exactly what's done and what's next — update it as you go so the
> next session (yours or anyone else's) never has to re-derive context from scratch.

---

## 1. Event context

- **Event:** Bharat Builds Tour, Event 02 — "Environmental Hacks" (WeMakeDevs × AWS)
- **Dates:** Oct 8–11, 2026 (online Thu–Sun), optional in-person build day **Oct 10 at DTU, Delhi**
- **Team:** Deepanshu Meena, DTU, B.Tech Software Engineering — solo unless a teammate is added
- **Track entering:** **Air** (see Decision 1 in `DECISIONS.md` for why, not Heat and Water)
- **Prize if track wins:** ₹2,00,000 cash + $2,000 AWS credits; 4 overall runners-up get $1,000 AWS credits each
- **Judging rubric (weighted toward these, in this order):**
  1. Idea and Impact — real environmental problem, real change for the people living with it
  2. Built on AWS — **mandatory**: must use at least one AWS open-source tool or be deployed on AWS
  3. Design and Usability — a stranger should understand it without explanation
  4. Execution — working beats polished; one real feature beats five fake ones
  5. Demo Video — 3 minutes, no live demo, the video is 100% of what judges see
- **Prior result to learn from:** First Commit hackathon entry (Sarkari Saathi) scored 11/30 — Idea & Impact was the weak point (1/8), judged "too generic." This project is deliberately designed to not repeat that mistake. Full reasoning is in `DECISIONS.md`.

---

## 2. The problem, in one paragraph

Delhi's outdoor workers — delivery riders, traffic police, construction labourers, street vendors —
spend 8–10 hours a day outside precisely when the city's AQI crosses 400+ (Oct–Nov, stubble-burning
season) and, separately, when heat stress is dangerous (pre-monsoon months). They have no way to
know their actual, accumulated exposure — only a city-wide AQI number that doesn't account for how
much *they personally* have breathed in, or a temperature reading that doesn't account for their
physical exertion. Nobody tells them *when to stop*, or *which route costs them less*.

## 3. What Kavach does

One safety copilot, three connected capabilities, all driven by real exposure science rather than
raw sensor display:

1. **Pollution exposure dose** — converts ambient PM2.5 + the worker's activity level + time outdoors
   into an actual inhaled dose, shown as something that means something ("cigarette-equivalents inhaled
   today"), not a raw AQI number they already ignore.
2. **"Take cover now" heat-stroke warning** — computes a WBGT-approximate heat-stress index from
   temperature, humidity and exertion level; when it crosses a danger threshold, pushes an alert with
   the nearest shaded/indoor point, not just "it's hot."
3. **Route comparison** — for a fixed demo corridor (2–3 real roads), scores each route option by
   cumulative heat + pollution exposure along it, and recommends the lowest-exposure route with the
   trade-off shown explicitly (e.g. "Route A: 12 min, AQI 410 avg. Route B: 15 min, AQI 290 avg —
   recommended").

An agent (Amazon Bedrock) fuses all three signals, decides when to alert vs. stay silent, and explains
recommendations in plain language.

## 4. Target users / demo personas

Three named personas used consistently across the pitch, UI and demo video:
- **Rohan**, a food-delivery rider, high exertion, long outdoor hours
- **Constable Singh**, Delhi traffic police, stationary-but-exposed, 8-hour shift
- **Mahesh**, a construction labourer, highest physical exertion, least phone access (so alerts should
  also reach a supervisor/dispatcher, not just the worker)

## 5. System architecture

```mermaid
flowchart LR
    subgraph DataIn[Scheduled data ingestion]
        CPCB[CPCB / OpenAQ\nlive AQI] --> L1[Lambda: ingest]
        FIRMS[NASA FIRMS\nfire/stubble-burning data] --> L1
        WX[Weather API\ntemp + humidity] --> L1
    end
    L1 --> DB[(DynamoDB\nlocality + worker state)]
    DB --> AGENT[Bedrock Agent\nfuses heat + pollution + route]
    UI[Amplify-hosted web UI\nmap + risk dashboard] --> APIGW[API Gateway]
    APIGW --> AGENT
    AGENT --> DB
    AGENT --> SNS[SNS: push alert\n"take cover now"]
    SNS --> Worker[Worker / dispatcher phone]
    AGENT --> APIGW --> UI
```

## 6. AWS service mapping

| Service | Purpose | Why this one (vs. alternative) |
|---|---|---|
| **Lambda** | Scheduled ingestion of AQI, fire-count, and weather data; also runs the heat/dose calculations | Serverless, free-tier friendly, no server to manage over a 4-day build. See Decision 8. |
| **DynamoDB** | Stores per-locality time-series readings, per-worker session state, route score cache | Serverless, pay-per-request fits free tier, simple key design for time-series + lookup |
| **Bedrock** | The agent that fuses heat + pollution + route signals and explains recommendations | Satisfies "Built on AWS" structurally (not just a config flag); avoids the non-AWS-model retirement risk from the last hackathon — see Decision 7 |
| **API Gateway** | HTTP interface between the Amplify frontend and the Lambda/Bedrock backend | Standard serverless API front door |
| **SNS** | Pushes the "take cover now" and route-alert notifications | Purpose-built for this, minimal setup |
| **Amplify Hosting** | Hosts the live map/dashboard frontend | Free tier, fast to deploy, judges can open a real URL |

## 7. Data sources

| Source | What it gives us | Access | Update frequency (plan) |
|---|---|---|---|
| CPCB / OpenAQ | Live station AQI / PM2.5 readings for Delhi localities | Public API (confirm exact endpoint before build day — see Open Questions) | Every 15–30 min |
| NASA FIRMS | Active fire detections (stubble-burning signal, upwind of Delhi) | Public API, free, needs a MAP_KEY (register ahead of time) | Every few hours |
| A weather API (OpenWeatherMap or similar) | Temperature, humidity for WBGT-approx calculation | Free tier | Every 15–30 min |

**Action before build day:** register for NASA FIRMS MAP_KEY and a weather API key now, not on the day — this is exactly the kind of "discovered too late" problem that cost time on the Gemini model issue last time.

## 8. Core calculations (the "hard to fake" part)

**Pollution dose** (per worker, per time window):
```
dose = PM2.5_ambient × breathing_rate(activity_level) × time_outdoors
```
`breathing_rate`: ~6 L/min resting, ~15 L/min light activity, ~25 L/min moderate-to-heavy labour
(standard occupational exposure ranges). Convert cumulative dose to a cigarette-equivalent using the
Berkeley Earth approximation (~22 µg/m³·hour of PM2.5 ≈ 1 cigarette) for the user-facing number.

**Heat stress (WBGT-approximate)**:
```
WBGT_approx = 0.7 × T_wet_bulb_est + 0.2 × T_globe_est + 0.1 × T_dry
```
Simplify for the hackathon using a standard heat-index approximation from temperature + humidity
(full WBGT needs globe/wet-bulb sensors we won't have); compare against OSHA/NIOSH moderate- and
heavy-work thresholds to set risk level (safe / caution / warning / danger).

**Route score** (per candidate route, demo corridor only):
```
route_cost = Σ (segment_length × local_PM2.5) + Σ (segment_length × local_heat_index) [weighted]
```
Lowest `route_cost` route is recommended; always show both options and both numbers, never just the
winner — that transparency is part of the "design and usability" pitch.

## 9. API design (draft)

- `GET /risk/current?worker_id=&lat=&lon=` → current pollution dose, heat risk, alert level
- `GET /route/compare?corridor_id=` → the 2–3 predefined routes with scores and the recommendation
- `POST /alert/ack` → worker/dispatcher acknowledges an alert (for the demo, logs state only)

Example response for `/risk/current`:
```json
{
  "worker_id": "rohan-demo",
  "pollution": { "aqi": 412, "dose_cigarette_equiv": 2.3, "risk": "high" },
  "heat": { "wbgt_approx": 31.2, "risk": "caution" },
  "recommendation": "Take a 15-minute break in shade within 10 minutes."
}
```

## 10. Demo scope decisions (MVP vs. stretch)

**MVP (must work for the video):**
- Live pull of real AQI + weather data for at least one real Delhi locality
- Dose and heat-index calculations running on real data, not hardcoded
- Fixed 2–3 route demo corridor with real scoring
- One alert firing live during a simulated/accelerated workday
- Deployed, with a real URL (Amplify)

**Stretch (only if time allows, in this order):**
1. A second and third persona shown simultaneously on the dashboard
2. A physical ESP32 + PM2.5 sensor (e.g. SDS011) feeding one live data point, to show real hardware
3. Expanding the route corridor beyond the fixed demo set

**Cut list if behind schedule (cut in this order):** stretch items above, then: reduce to one persona,
then: reduce route comparison to a static pre-scored pair instead of live scoring, then: reduce heat
module to a simpler index if WBGT math proves fiddly — pollution dose + alert is the one feature that
must survive no matter what.

## 11. Build plan (Oct 8–11)

- **Thu (Oct 8):** Repo scaffold, AWS account/free-tier setup, register API keys (FIRMS, weather),
  Lambda ingestion skeleton pulling real AQI data into DynamoDB. Confirm CPCB/OpenAQ access works.
- **Fri (Oct 9):** Pollution dose module working end-to-end (real data → dose → cigarette-equivalent).
  Heat WBGT-approx module working. Start the Bedrock agent wiring.
- **Sat (Oct 10 — DTU build day):** Route comparison module (fixed corridor), agent fusing all three
  signals, frontend map UI on Amplify. Use mentor time here specifically to sanity-check the heat/dose
  math and the AWS architecture, since mentors are in the room.
- **Sun (Oct 11):** SNS alert wiring, polish the UI to the one "striking screen," record the 3-minute
  demo video, write README.md and DECISIONS.md (update from drafts in this repo), submit with time to
  spare — not at the deadline.

## 12. Repo structure (planned)

```
kavach/
├── README.md
├── DECISIONS.md
├── BLUEPRINT.md              (this file)
├── template.yaml              # AWS SAM template
├── backend/
│   ├── ingest/                # Lambda: pulls AQI/FIRMS/weather into DynamoDB
│   ├── risk/                  # Lambda: dose + WBGT calculations
│   ├── route/                 # Lambda: route scoring
│   └── agent/                 # Bedrock agent wiring + tool definitions
├── frontend/                  # Amplify-hosted map/dashboard
├── data/                      # fixed demo corridor definition, persona configs
└── tests/
```

## 13. Judging-criteria alignment (self-check before submitting)

| Criterion | How Kavach answers it |
|---|---|
| Idea and Impact | Named, vulnerable persona; a real inhaled-dose number, not an abstract index; matches the Air track's own wording ("warn the people most exposed... change what happens on bad days") |
| Built on AWS | Lambda, DynamoDB, Bedrock, API Gateway, SNS, Amplify all structurally load-bearing, not swappable |
| Design and Usability | One screen: live map, two route options with real numbers, a risk dashboard a stranger can read in seconds |
| Execution | MVP list above is scoped to be fully real and working, not five half-features |
| Demo Video | Stakes-first open (a real number: "X cigarettes by 6pm"), split-persona view, a live alert firing on camera |

## 14. Open questions / confirm before or on Day 1

- [ ] Exact CPCB/OpenAQ endpoint and rate limits for Delhi stations — confirm access works before relying on it
- [ ] NASA FIRMS MAP_KEY registered
- [ ] Weather API key registered
- [ ] Team size final (solo vs. adding a teammate) — affects how much of the stretch list is realistic
- [ ] Which Bedrock model to use — pick one and pin it explicitly in config (lesson from the Gemini retirement issue: never hardcode a model name without an env var)

---

## 15. Status (update this section as you build — this is what makes handoff actually work)

**Last updated:** 2026-10-02 — core engine built and tested locally, not yet deployed.

- [x] Repo scaffolded (`src/kavach/`, `tests/`, SAM template, CI)
- [ ] AWS account / free tier set up
- [ ] API keys registered (FIRMS, weather) — not required to run the demo locally, only for live data
- [x] Ingestion Lambda written (`lambda_handler.ingest_handler`) — works locally, not yet deployed/scheduled
- [x] Pollution dose module working (`risk.py`, unit-tested)
- [x] Heat index (WBGT-approx) module working (`risk.py`, unit-tested)
- [x] Route comparison module working (`corridor.py`, fixed demo corridor, unit-tested)
- [x] Agent wired with Bedrock + deterministic offline fallback (`agent.py`)
- [x] Frontend built (`static/index.html`, Leaflet map + dashboard) — runs locally, not yet deployed to Amplify
- [ ] SNS alerts firing (topic defined in `template.yaml`, not yet wired to a real publish call)
- [ ] Demo video recorded
- [x] README.md and DECISIONS.md finalized for current state (will need one more pass after deployment for the live URL)
- [ ] Submitted

**Next concrete steps, in order:** (1) `sam build && sam deploy --guided` to get a live URL,
(2) confirm Bedrock model access in the AWS account and set `BEDROCK_MODEL_ID` to whatever is
actually available, (3) wire the SNS publish call into the `/api/risk/current` and `/api/simulate/workday`
handlers when `take_cover` is true, (4) record the demo video using the CLI/dashboard numbers as the script.

**If you're picking this up fresh:** check the boxes above, read Decision log in `DECISIONS.md` for
*why* each choice was made (and what was rejected), and don't re-litigate a decision already made here
unless something concrete has changed (an API turns out inaccessible, a teammate joins, etc.).
