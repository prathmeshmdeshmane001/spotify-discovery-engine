export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader("Access-Control-Allow-Credentials", true);
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS,PATCH,DELETE,POST,PUT");
  res.setHeader(
    "Access-Control-Allow-Headers",
    "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
  );

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  let body = req.body;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch {
      body = {};
    }
  }

  const { vibeLabel, vibeSeed, tracks } = body || {};
  const list = Array.isArray(tracks) ? tracks.slice(0, 10) : [];

  const defaultLinerNotes = (track) => {
    const templates = [
      `Expands on ${vibeLabel || "this playlist"} with deeper ${track.mood || "melodic"} textures and raw atmospheric production.`,
      `Pushes past repetitive rotation by introducing emerging sound design while maintaining the ${track.mood || "introspective"} groove.`,
      `Recommended by the Discovery Dial to break algorithmic sameness through punchy rhythms and unexpected genre crossover.`,
      `Bridges familiar radio standards with underground artistry, keeping the energy aligned at ${track.energy || 3}/5.`,
      `Adds dynamic range to your queue — preserving mood consistency without repeating the usual catalog staples.`,
    ];
    const hash = (track.title || "").split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
    return templates[hash % templates.length];
  };

  const fallbackResponse = (debugInfo) =>
    res.status(200).json({
      source: "fallback",
      debug: debugInfo,
      reasons: list.map((t) => ({
        id: t.id,
        why: defaultLinerNotes(t),
      })),
    });

  const groqKey = process.env.GROQ_API_KEY;
  if (!groqKey) return fallbackResponse("NO_GROQ_KEY");
  if (list.length === 0) return fallbackResponse("NO_TRACKS");

  const prompt = `You are an elite Spotify editorial music critic writing one-line liner notes for an AI-powered Discovery Playlist.
The chosen vibe is "${vibeLabel || "Discovery Mix"}" — ${vibeSeed || "dynamic, curated sound"}.

Below are tracks recommended to break the listener out of algorithmic stagnation.
For EACH track, write ONE concise sentence (10-18 words max) explaining why this track fits the vibe while expanding the listener's musical horizon.

RULES:
- Be specific about sound, mood, era, or production texture.
- Do NOT use second-person pronouns ("you", "your").
- Do NOT repeat the track title or artist name.
- Return ONLY valid JSON array with format: [{"i": 1, "why": "..."}, {"i": 2, "why": "..."}]

Tracks:
${list.map((t, i) => `${i + 1}. "${t.title}" by ${t.artist} — Mood: ${t.mood || "vibrant"}, Energy: ${t.energy || 3}/5, Year: ${t.year || 2024}`).join("\n")}`;

  try {
    const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${groqKey}`,
      },
      body: JSON.stringify({
        model: process.env.GROQ_MODEL || "openai/gpt-oss-20b",
        temperature: 0.7,
        max_tokens: 500,
        messages: [{ role: "user", content: prompt }],
      }),
    });

    if (!r.ok) {
      return fallbackResponse(`GROQ_HTTP_${r.status}`);
    }

    const data = await r.json();
    let text = data?.choices?.[0]?.message?.content?.trim() || "";
    text = text.replace(/```json/gi, "").replace(/```/g, "").trim();

    const parsed = JSON.parse(text);
    if (!Array.isArray(parsed)) return fallbackResponse("NOT_ARRAY");

    const reasons = list.map((t, idx) => {
      const match = parsed.find((p) => Number(p.i) === idx + 1);
      return {
        id: t.id,
        why: match?.why || defaultLinerNotes(t),
      };
    });

    return res.status(200).json({ source: "groq", reasons });
  } catch (err) {
    return fallbackResponse(`EXCEPTION_${err.message}`);
  }
}
