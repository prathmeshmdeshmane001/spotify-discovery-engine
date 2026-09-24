# Brag Plan: Spotify Discovery Engine

## What is this app?
An end-to-end research pipeline that scrapes and hand-collects 456 real Spotify user reviews from 5 sources, classifies each one through a Groq LLM (llama-3.3-70b) against a 7-field taxonomy, and surfaces the frustration data that drove the "Discovery Dial" feature concept — running daily on GitHub Actions.

## The angle
This is a PM portfolio piece: the video is a 20-second proof-of-rigor story. The premise: "Spotify's recommendations are stale — and I can prove it with data." Every scene shows real numbers, real taxonomy fields, and the actual pipeline stages. No generic SaaS language; the claims come straight from the project's insights (456 reviews, 34.9% discovery-related, stale_recommendations as top frustration, active_explorer segment, Discovery Dial as the outcome).

## Hook (first 2-3 seconds)
Big display type on Spotify-dark: **"Your Daily Mix is the same songs. Again."** — then a stamp: **"456 real user reviews agree."** The hook is the shared user pain, backed instantly by the project's data credential.

## Key moments (the middle)
- **The pipeline lights up:** five nodes — Ingest → Classify → Segment → Aggregate → Insights — energize left to right, with source chips popping in (Play Store ·353, Reddit, App Store, Forums, X) while Groq llama-3.3-70b is named as the classifier engine.
- **The classifier in action (centerpiece):** a real-looking review card — *"My daily mixes are just the same songs on repeat every week. I want new artists."* — gets classified live: the red `stale_recommendations` tag slams on, then the green `active_explorer` segment tag, `discovery_related: YES`, and `sentiment: frustrated` snap in one by one.
- **The findings count up:** 159 discovery-related · 34.9% of reviews · 53 active_explorer × stale_recommendations crosstab — the exact numbers that drove the product decision.

## Outro / punchline
**"Those numbers became a feature."** → Discovery Dial concept lockup, one line: *"A playlist-level novelty dial, built on what users actually said."* Tech footer: Python · Groq · Supabase · GitHub Actions · Streamlit.

## User flow worth showing
The Streamlit demo's happy path: a review sits unclassified → the classifier runs → the review card returns wearing its 7-field taxonomy tags → session insights update. Scene 3 recreates exactly this: review card in, tags out, insights counter ticks up.

## Tone
- Preset: polished
- Creative direction: PM portfolio case-study film — quiet confidence, data-forward, Spotify-dark aesthetic
- Interpretation: fewer scenes, longer holds, clean reveals. Confidence comes from restraint and real numbers, not speed or jokes.

## Format: landscape — 1920x1080
## Duration: 22 seconds

## Visual identity (from the project)
- Background: #121212
- Card surface: #181818
- Accent: #1DB954 (Spotify green)
- Alert/red: #ff6b6b (frustration tags)
- Secondary text: #B3B3B3
- Text: #FFFFFF
- Display font: geometric grotesque in the spirit of Spotify Circular (e.g. Outfit / Figtree), tight tracking
- Body font: same family, regular weight
- Strongest visual element: the review card with its pill-shaped taxonomy tags (border-left 4px green, #181818 card, rounded 12px) — recreated faithfully from the Streamlit CSS

## Share copy (draft)
I turned 456 real Spotify reviews into product evidence — scraped, LLM-classified, and aggregated daily on GitHub Actions. The findings became the Discovery Dial concept.

## Audio direction
- Role: warm professional bed with restrained motion-matched accents
- Music: modern minimal electronic bed, ~100-110 BPM, confident and clean (resolved via media-use; cues detected at composition time)
- Music treatment: low volume under the hook, gentle lift when the pipeline energizes, subtle swell on the findings count-up, clean fade on the outro
- Music cue guidance: to be detected at composition time; target strong cues for the tag-slam in Scene 3 and the stat count-up in Scene 4
- Audio-reactive treatment: subtle; card glow may breathe with the music energy — no waveform bars
- SFX posture: sparse; soft UI ticks for tag reveals, one satisfying stamp/thud for the hook stat, light whoosh on transitions
- Audio-coupled moments: hook line types/settles; source chips pop one by one; taxonomy tags snap in sequentially; stat counters tick up
- Restraint rule: nothing loud or comedic — the audio should feel like a well-made product film

## Storyboard

### Scene 1 — Hook — 3s
Black #121212 screen. Line 1 in large white display type: "Your Daily Mix is the same songs." ("Again." lands a beat later in green). A small green stamp appears bottom-center: "456 real user reviews agree." Fast-in, then hold — the line settles with time to read.
Sequential/interaction: yes — "Again." and the stamp arrive one after the other, ~0.6s apart, then the full set holds.
Audio intent: quiet confidence; bed starts low, one soft stamp hit on "Again."
Audio-coupled idea: stamp/thud on the stat line landing.
Music: minimal electronic bed, low volume.
Transition mood: clean → Scene 2

### Scene 2 — The pipeline — 5s
Headline: "456 reviews. 5 sources. One pipeline." Below it, five pipeline nodes in a row — Ingest → Classify → Segment → Aggregate → Insights — light up left to right. Above the Ingest node, five source chips pop in sequentially: Google Play ·353, Reddit, App Store, Forums, X. Under Classify, a small label: "Groq · llama-3.3-70b". Under Aggregate: "GitHub Actions · daily".
Sequential/interaction: yes — source chips pop one by one (~0.35s apart, short labels so pacing is fine), then pipeline nodes energize left to right (~0.4s apart).
Audio intent: momentum builds; bed lifts slightly.
Audio-coupled idea: chip pops and node energize matched to the beat grid where possible.
Music: same bed, rising energy.
Transition mood: clean slide → Scene 3

### Scene 3 — The classifier (centerpiece) — 6s
A review card faithful to the Streamlit UI (#181818, 12px radius, 4px green left border): a quote from a frustrated user — *"My daily mixes are just the same songs on repeat every week. I want new artists."* A green pill button "Classify with Groq LLM" gets a simulated cursor click. Then the taxonomy tags snap onto the card one by one: red pill `stale_recommendations`, green-outline pill `segment: active_explorer`, green pill `discovery_related: YES`, grey pill `sentiment: frustrated`. Each holds; the full tagged card stays settled.
Sequential/interaction: yes — cursor click, then 4 tags snap in one by one (~0.5s apart), full set holds for reading.
Audio intent: the payoff moment — satisfying, precise.
Audio-coupled idea: soft UI tick per tag snap, click sound on the button.
Music: bed continues, focused.
Transition mood: soft crossfade → Scene 4

### Scene 4 — The findings — 4s
Three stat blocks count up in sequence: **159** discovery-related reviews · **34.9%** of all reviews · **53** active_explorer × stale_recommendations (the crosstab headline). Small caption under the row: "The evidence behind the product decision."
Sequential/interaction: yes — counters tick up one after another, each resolving quickly and holding.
Audio intent: crescendo — this is the data landing.
Audio-coupled idea: counter ticks matched to music energy.
Music: bed at its peak energy.
Transition mood: soft crossfade → Scene 5

### Scene 5 — Outro — 4s
Line in white: "Those numbers became a feature." The Discovery Dial lockup appears — a simple circular dial graphic with a green needle, labeled "Discovery Dial — playlist-level novelty control." Tech footer in grey small caps: Python · Groq · Supabase · GitHub Actions · Streamlit. Hold, then gentle fade.
Sequential/interaction: yes — dial draws in, footer fades up last.
Audio intent: resolution; bed fades clean.
Audio-coupled idea: subtle whoosh as the dial draws.
Music: fade out.
Transition mood: soft fade → end

**Music mood for this video:** confident, minimal, modern electronic — clean and professional
**Audio summary:** a low confident bed that lifts as the pipeline energizes, peaks at the findings count-up, and resolves cleanly under the Discovery Dial outro, with sparse UI ticks and one stamp hit marking the moments that matter.
