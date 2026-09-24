# Hyperframes Composition Brief: Spotify Discovery Engine

## Objective
Create a short, polished, portfolio-grade explanation video for the Spotify Discovery Engine — a 22-second case-study film showing how 456 real Spotify reviews became product evidence and a feature concept.

## Output
- Composition directory: `brag-output-2026-09-19-220420/composition/`
- Rendered video: `brag-output-2026-09-19-220420/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 22 seconds

## Source Material
- Project root: `/Users/prathameshdeshmane/spotify-discovery-engine-main`
- Primary files read: `README.md`, `streamlit_app.py` (theme CSS + review-card/tag styles), `insights.md`, project structure
- Product name: Spotify Discovery Engine
- Tagline / strongest claim: "456 real user reviews. 34.9% say music discovery is broken. Those numbers became a feature."
- Key UI or visual moment to recreate: the Streamlit review card — #181818 surface, 12px radius, 4px #1DB954 left border — with pill-shaped taxonomy tags (`stale_recommendations` in #ff6b6b red, `active_explorer` in green outline, `discovery_related: YES` solid green)
- Copy that must appear verbatim:
  - "456 real user reviews agree."
  - "Classify with Groq LLM"
  - "159" discovery-related reviews · "34.9%" of all reviews · "53" active_explorer × stale_recommendations
  - "Those numbers became a feature."
  - Tech footer: Python · Groq · Supabase · GitHub Actions · Streamlit

## Creative Direction
- Tone preset: polished
- Creative direction: PM portfolio case-study film — quiet confidence, data-forward, Spotify-dark aesthetic
- Interpretation: fewer scenes, longer holds, clean reveals. Confidence comes from restraint and real numbers, not speed or jokes. Motion is precise and professional; nothing comedic.
- Angle: The video is a 20-second proof-of-rigor story: "Spotify's recommendations are stale — and I can prove it with data." Every scene shows real numbers, real taxonomy fields, and the actual pipeline stages, ending on the Discovery Dial concept the data drove.
- Hook: Big display type on Spotify-dark: "Your Daily Mix is the same songs." then "Again." in green, then the stamp "456 real user reviews agree."
- Outro / punchline: "Those numbers became a feature." → Discovery Dial lockup with a circular dial graphic + tech footer.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Waveform/equalizer visuals or heavy pulsing

## Visual Identity
- Background: #121212
- Card surface: #181818
- Text: #FFFFFF
- Secondary text: #B3B3B3
- Accent: #1DB954 (Spotify green; hover #1ed760)
- Alert/red: #ff6b6b (frustration tags)
- Display font: geometric grotesque in the spirit of Spotify Circular (e.g. Outfit or Figtree), tight tracking
- Body font: same family
- Visual references from the project: Streamlit review card + pill tags, green round-pill buttons (500px radius), Spotify metric values in green, dark tab chips (#282828)

## Storyboard
Use the storyboard in `brag-output-2026-09-19-220420/brag-plan.md` as the creative contract.

Scene summary:
1. Hook — 3s — "Your Daily Mix is the same songs. Again." + stamp "456 real user reviews agree."
2. The pipeline — 5s — 5 source chips pop in, 5 pipeline nodes energize left to right (Ingest → Classify → Segment → Aggregate → Insights), labels "Groq · llama-3.3-70b" and "GitHub Actions · daily"
3. The classifier (centerpiece) — 6s — faithful review card, simulated cursor clicks "Classify with Groq LLM", 4 taxonomy tags snap on one by one, full set holds
4. The findings — 4s — three stat counters tick up: 159 · 34.9% · 53, caption "The evidence behind the product decision."
5. Outro — 4s — "Those numbers became a feature." + Discovery Dial circular dial lockup + tech footer, gentle fade out

## Audio
- Audio role: warm professional bed with restrained motion-matched accents
- Audio arc: bed starts low under the hook, lifts as the pipeline energizes, peaks at the findings count-up, resolves and fades under the Discovery Dial outro
- Music: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3` (polished/cinematic track per brag audio reference), already copied to `composition/assets/music/`
- Music treatment: volume ~0.28-0.35; low under hook, gentle lift in Scene 2, peak presence Scene 4, clean fade over the last ~2s
- Music cue guidance: bundled track — read `assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.md` / `.json` for tempo, strongCues, and beat grid. Target 1-3 strong-cue locks: the tag-slam in Scene 3 and the stat count-up in Scene 4 are the best candidates. Sequential reveals (source chips, tags) snap to consecutive beats only where spacing stays ≥0.35s for readable text.
- Audio-reactive treatment: subtle; card glow / dial presence may breathe gently with RMS. No waveform bars, no strobing.
- Audio-coupled moments:
  - Scene 1 hook — stamp/thud accent when "456 real user reviews agree." lands
  - Scene 2 — soft pops for source chips, one accent per pipeline node (accent first/last only if busy)
  - Scene 3 — cursor click sound on the button, soft UI tick per taxonomy tag snap
  - Scene 4 — counter ticks rising with music energy
  - Scene 5 — subtle whoosh as the dial draws, music fade
- SFX selection guidance: `assets/sfx/sfx-analysis.md` — polished tone = minimal, 2-3 very subtle SFX per scene at most, low HF-risk files, nothing aggressive
- Exact SFX choice: Hyperframes chooses filenames, timestamps, density, and volume based on the implemented animation; copy chosen files into `composition/assets/sfx/`
- Audio files: music staged in `composition/assets/music/`; stage SFX into `composition/assets/sfx/`

## Hyperframes Instructions
Load the composition-building Hyperframes domain skills — `hyperframes-core` (composition contract + `data-*` timing), `hyperframes-animation` (motion), `hyperframes-creative` (design spec, beats, audio-reactive), `hyperframes-keyframes` (seek-safe keyframes), and `hyperframes-cli` (lint/check/render). /brag is its own workflow: do not enter the `hyperframes` entry-point intent interview and do not route into its generic promo / launch-video workflow. Prefer native Hyperframes conventions over anything in `/brag`.

Requirements:
- Show at least one real UI, copy, or visual element from the source project (the Scene 3 review card with its taxonomy tags is the mandated recreation, faithful to the Streamlit CSS).
- Keep all text readable — fast-in then hold; every readable line gets its settle time (short label ≥0.8s, sentences ≥0.3s/word).
- Keep the video within 15-25 seconds.
- Include the planned music/SFX layer.
- Treat `/brag` audio notes as guidance, not a fixed cue sheet.
- Treat music cue metadata as optional timing hints; readability and pacing win over beat sync.
- Major reveals may move toward nearby strong cues within ~0.15s; smaller entrances within ~0.10s; 1-3 strong cue locks total.
- Honor planned music treatment (low start, lift, peak, clean fade-out at the end).
- Use local assets for audio; never absolute paths.
- Run `hyperframes check` before render — it is brag's single gate.
