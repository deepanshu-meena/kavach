# Design Decisions

Short records of the choices behind Kavach: what we chose, why, and what we gave up. Read alongside
`BLUEPRINT.md` (the technical spec) and `README.md` (the user-facing description).

## 1. Track: Air, not Heat and Water, despite the project covering both

**Decision:** Submit under the **Air** track, even though Kavach includes a heat-stroke module.
**Why:** The Air track's own description — "warn the people most exposed to it, and change what
happens on the bad days" — matches this project almost word for word. Timing matters too: the event
runs Oct 8–11, Delhi's pollution season (post-monsoon stubble burning), not its heat season (which
peaks May–June). Judges will feel the AQI angle more than the heat angle that week.
**Trade-off:** The heat module might read as a slight tangent to an Air-track judge. Mitigation: frame
it explicitly in the pitch as "the same exposure engine catches the other thing killing outdoor
workers too" — a demonstration of depth, not scope creep.

## 2. Persona: outdoor workers, not "anyone" or "a parent deciding for their child"

**Decision:** Build for three named outdoor-worker personas (delivery rider, traffic police,
construction labourer), not a general-audience AQI app.
**Why:** The last hackathon's direct feedback was "idea very basic, used in many projects" — a
general-purpose tool. Outdoor workers are a narrower, higher-stakes, more specific group who have no
choice about their exposure, which is the "small problem solved well beats a big one solved vaguely"
standard the rubric states outright.
**Alternative considered:** A parent-facing "is it safe for my kid to play outside" app — rejected as
still too close to a generic consumer AQI dashboard, the most overdone category in this track.

## 3. Heat index: WBGT-approximation, not full WBGT, not raw temperature

**Decision:** Compute a WBGT-*approximate* index from temperature + humidity + exertion level, rather
than a full Wet Bulb Globe Temperature reading (which needs a globe thermometer sensor) or a plain
"it's 43°C" display.
**Why:** Raw temperature doesn't account for who's actually at risk — a resting person and a labourer
in the same heat face very different danger. Full WBGT needs hardware we won't have in four days.
The approximation is a documented, real occupational-health method, not invented.
**Trade-off:** Less precise than instrumented WBGT. We say this plainly in the README rather than
implying lab-grade accuracy.

## 4. Pollution exposure: a dose calculation, not a static AQI display

**Decision:** Convert ambient PM2.5 × breathing rate (by activity level) × time outdoors into a
cumulative dose, shown as cigarette-equivalents.
**Why:** Everyone already has access to an AQI number; it's not acted on because it's abstract. A
dose that accumulates over a shift and converts to something visceral is the same move that worked for
other hackathon placements (turning a technical reading into a number people feel).
**Trade-off:** The cigarette-equivalent conversion is an approximation (Berkeley Earth's ~22 µg/m³·hour
≈ 1 cigarette), not a precise medical claim — stated as such in the app and docs.

## 5. Data sources: CPCB/OpenAQ + NASA FIRMS + a weather API, not a single bundled source

**Decision:** Combine three separate public data sources rather than one all-in-one weather/AQI API.
**Why:** NASA FIRMS fire-detection data is what lets the system anticipate *tomorrow's* stubble-burning
smoke, not just report today's AQI after the fact — this is the forward-looking signal that makes the
alert useful before exposure happens, not just a readout of harm already done.
**Trade-off:** Three integrations instead of one means more can go wrong in a short build. Mitigation:
Day 1 of the build plan is specifically about confirming all three sources work before building logic
on top of them, instead of discovering an access problem late (the Gemini-model-retirement mistake
from the last hackathon is the cautionary example for this).

## 6. Routing: a fixed demo corridor, not a citywide live routing engine

**Decision:** Score 2–3 predefined real routes in one fixed area, rather than building a full
citywide routing engine (e.g., a hosted OSRM instance with arbitrary start/end points).
**Why:** A full routing engine is a multi-week project on its own. A fixed corridor still does the
real calculation — integrating heat + pollution along each path — it just doesn't generalize to any
two points in Delhi yet. Judges are told explicitly to value "one feature that runs" over "five that
almost do."
**Trade-off:** Less impressive as a general-purpose product in the demo. Mitigation: state this
limitation directly in the video and README as a scoping decision, and name "expand to citywide
routing" as the clear next step — judges respond better to an honest scope line than to a demo that
quietly fakes generality.

## 7. Model/agent: Amazon Bedrock, not an external provider via Strands/LiteLLM

**Decision:** Use Amazon Bedrock directly for the agent, rather than repeating the First Commit
hackathon's pattern of an AWS-open-source agent framework calling an external free-tier model.
**Why:** Two reasons. First, "Built on AWS" is now explicitly mandatory to win a prize in this event —
a Bedrock-hosted model makes AWS usage structural, not a config flag pointed at a non-AWS provider.
Second, the last hackathon lost real build time mid-flight when a third-party model (Gemini) was
retired without warning; Bedrock avoids repeating that specific failure mode.
**Trade-off:** Less flexibility to swap in a free non-AWS model later. Mitigation: still pin the exact
Bedrock model ID in an environment variable, never hardcoded, in case a specific Bedrock model is
deprecated or access needs to change.

## 8. AWS architecture: serverless (Lambda/DynamoDB/SNS/API Gateway/Amplify), not a single EC2 app

**Decision:** Build on Lambda, DynamoDB, SNS, API Gateway and Amplify Hosting rather than one
always-on server.
**Why:** Fits inside the AWS Free Tier for a weekend build, requires no server management during a
time-constrained hackathon, and — same reasoning as Decision 7 — makes "Built on AWS" five services
deep rather than one dependency swapped in. The last hackathon scored 3/10 on AWS Usage specifically
because the AWS piece was optional/swappable; this architecture makes it load-bearing.
**Trade-off:** More moving pieces to wire together than a single app. Mitigation: the Day 1 build-plan
step is scaffolding and confirming all pieces talk to each other before adding feature logic.

## 9. Hardware (ESP32 + PM2.5 sensor): stretch goal, not MVP

**Decision:** A physical sensor feeding one real data point is explicitly a stretch item, not part of
the must-work MVP.
**Why:** Real hardware is a strong signal to judges (it's what pushed FreshTrace to a runner-up finish
last event) — it's "hard to fake." But hardware introduces its own failure modes (shipping, wiring,
calibration) that can eat a disproportionate share of a 4-day build if treated as core.
**Trade-off:** If it doesn't make it in, the core pitch still stands entirely on the public-API data
pipeline, which is itself a real, verifiable technical component.

## 10. What gets cut first if time runs short

**Decision:** A pre-agreed cut order (see `BLUEPRINT.md` section 10), rather than deciding under
pressure on the last day.
**Why:** The rubric rewards "does it work" over "does it almost do five things." Deciding the
priority order now — stretch features first, then personas, then route scoring, with pollution dose +
alert protected as the one feature that must survive — avoids a last-minute scramble that leaves
everything half-working instead of one thing fully working.

## 11. Offline fallback for every external data source, not a hard dependency

**Decision:** Every live data call (OpenAQ, Open-Meteo, NASA FIRMS, Bedrock) has a documented,
deterministic fallback to bundled sample data or a template explanation, rather than raising an
error the demo can't recover from.
**Why:** The First Commit hackathon lost real build time to an unannounced model retirement with no
graceful handling. This project is built from the start so that a missing API key, a network hiccup,
or an unavailable Bedrock model degrades the explanation quality, not the whole demo. `tests/` cover
the fallback path directly, not just the happy path.
**Trade-off:** The offline numbers are realistic-but-not-live when no keys are configured. This is
stated plainly in the README and in the UI's "explanation source" label (bedrock vs. fallback) rather
than hidden.

## 12. One FastAPI app, reused on Lambda via Mangum, not a duplicated router

**Decision:** `lambda_handler.py` wraps the same FastAPI app from `api.py` with Mangum, instead of
hand-writing a second set of route handlers for API Gateway (which the First Commit project did).
**Why:** One source of truth for the API surface means a route added locally works on Lambda for
free, and there's one test suite (`tests/test_api.py`) instead of two to keep in sync.
**Trade-off:** Slightly more complex cold-start behaviour than a hand-rolled minimal handler, which
is an acceptable cost at this scale.

## What we'd do next

Citywide routing, more personas, a real hardware sensor, a pilot with an actual delivery platform or
the Delhi Traffic Police, and multi-language alerts (Hindi, given the target users).
