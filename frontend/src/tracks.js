// Curated track pool for the Spotify Discovery Dial
// familiarity: "familiar" = mainstream rotation, "new" = deeper cuts & algorithmic discoveries

export const VIBES = [
  { id: "indie", label: "Indie & Alternative", seed: "warm guitars, lo-fi, introspective, melancholic" },
  { id: "ambient", label: "Ambient & Electronic", seed: "spacious, textural, calming, cinematic" },
  { id: "techno", label: "Late-Night Underground", seed: "driving, hypnotic, dark basslines, club ready" },
  { id: "hyperpop", label: "Hyperpop & Future Pop", seed: "glitchy, maximal, pitch-shifted, playful" },
  { id: "jazz", label: "Nu-Jazz & Lo-Fi Beats", seed: "soulful Rhodes, organic drums, brass accents" },
  { id: "shoegaze", label: "Shoegaze & Dream Pop", seed: "hazy, reverb-soaked guitars, ethereal vocals" },
];

export const TRACKS = [
  // ── INDIE ──────────────────────────────────────────────────────────
  { id: "i1", title: "Apocalypse", artist: "Cigarettes After Sex", vibe: "indie", familiarity: "familiar", energy: 2, mood: "melancholy", year: 2017, duration: "4:50", cover: "from-blue-900 to-indigo-950" },
  { id: "i2", title: "Two Slow Dancers", artist: "Mitski", vibe: "indie", familiarity: "familiar", energy: 2, mood: "melancholy", year: 2018, duration: "3:59", cover: "from-purple-900 to-black" },
  { id: "i3", title: "The Less I Know The Better", artist: "Tame Impala", vibe: "indie", familiarity: "familiar", energy: 4, mood: "groovy", year: 2015, duration: "3:36", cover: "from-pink-900 to-rose-950" },
  { id: "i4", title: "Space Song", artist: "Beach House", vibe: "indie", familiarity: "familiar", energy: 2, mood: "dreamy", year: 2015, duration: "5:20", cover: "from-cyan-900 to-blue-950" },
  { id: "i5", title: "Kyoto", artist: "Phoebe Bridgers", vibe: "indie", familiarity: "familiar", energy: 3, mood: "yearning", year: 2020, duration: "3:04", cover: "from-slate-800 to-slate-950" },
  { id: "i6", title: "Crisis Fest", artist: "Sunflower Bean", vibe: "indie", familiarity: "new", energy: 4, mood: "restless", year: 2018, duration: "3:12", cover: "from-amber-900 to-orange-950" },
  { id: "i7", title: "Quarter to Three", artist: "Hovvdy", vibe: "indie", familiarity: "new", energy: 2, mood: "warm", year: 2021, duration: "2:45", cover: "from-yellow-900 to-stone-900" },
  { id: "i8", title: "Hold U", artist: "Indigo De Souza", vibe: "indie", familiarity: "new", energy: 3, mood: "raw", year: 2021, duration: "4:15", cover: "from-red-900 to-fuchsia-950" },
  { id: "i9", title: "Soft to Be Strong", artist: "Marika Hackman", vibe: "indie", familiarity: "new", energy: 2, mood: "introspective", year: 2019, duration: "3:40", cover: "from-teal-900 to-emerald-950" },
  { id: "i10", title: "Cellophane Memories", artist: "Wishy", vibe: "indie", familiarity: "new", energy: 3, mood: "hazy", year: 2024, duration: "3:22", cover: "from-sky-900 to-indigo-900" },

  // ── AMBIENT ─────────────────────────────────────────────────────────
  { id: "a1", title: "An Ending (Ascent)", artist: "Brian Eno", vibe: "ambient", familiarity: "familiar", energy: 1, mood: "serene", year: 1983, duration: "4:24", cover: "from-blue-950 to-black" },
  { id: "a2", title: "Avril 14th", artist: "Aphex Twin", vibe: "ambient", familiarity: "familiar", energy: 1, mood: "wistful", year: 2001, duration: "2:05", cover: "from-emerald-950 to-black" },
  { id: "a3", title: "Says", artist: "Nils Frahm", vibe: "ambient", familiarity: "familiar", energy: 2, mood: "building", year: 2013, duration: "8:18", cover: "from-indigo-950 to-neutral-900" },
  { id: "a4", title: "Substrata", artist: "Biosphere", vibe: "ambient", familiarity: "new", energy: 1, mood: "glacial", year: 1997, duration: "6:10", cover: "from-cyan-950 to-slate-900" },
  { id: "a5", title: "Subaqueous Flow", artist: "Loscil", vibe: "ambient", familiarity: "new", energy: 1, mood: "submerged", year: 2019, duration: "5:44", cover: "from-teal-950 to-slate-950" },
  { id: "a6", title: "Wholeness", artist: "Green-House", vibe: "ambient", familiarity: "new", energy: 2, mood: "verdant", year: 2020, duration: "3:50", cover: "from-green-950 to-neutral-900" },
  { id: "a7", title: "Tirian", artist: "Hilyard", vibe: "ambient", familiarity: "new", energy: 1, mood: "drifting", year: 2021, duration: "4:30", cover: "from-slate-900 to-zinc-950" },

  // ── TECHNO ──────────────────────────────────────────────────────────
  { id: "t1", title: "Spastik", artist: "Plastikman", vibe: "techno", familiarity: "familiar", energy: 4, mood: "hypnotic", year: 1993, duration: "9:18", cover: "from-zinc-900 to-black" },
  { id: "t2", title: "Windowlicker", artist: "Aphex Twin", vibe: "techno", familiarity: "familiar", energy: 4, mood: "warped", year: 1999, duration: "6:07", cover: "from-stone-900 to-neutral-950" },
  { id: "t3", title: "Glue", artist: "Bicep", vibe: "techno", familiarity: "familiar", energy: 4, mood: "euphoric", year: 2017, duration: "4:29", cover: "from-fuchsia-950 to-black" },
  { id: "t4", title: "Sicko Cell", artist: "Anz", vibe: "techno", familiarity: "new", energy: 5, mood: "bright", year: 2021, duration: "4:48", cover: "from-rose-900 to-black" },
  { id: "t5", title: "Tidal", artist: "Peverelist", vibe: "techno", familiarity: "new", energy: 4, mood: "rolling", year: 2020, duration: "5:12", cover: "from-violet-950 to-slate-950" },
  { id: "t6", title: "Panorama Bar Loop", artist: "Efdemin", vibe: "techno", familiarity: "new", energy: 4, mood: "dubby", year: 2018, duration: "6:33", cover: "from-neutral-900 to-zinc-950" },

  // ── HYPERPOP ────────────────────────────────────────────────────────
  { id: "h1", title: "Money Machine", artist: "100 gecs", vibe: "hyperpop", familiarity: "familiar", energy: 5, mood: "chaotic", year: 2019, duration: "2:21", cover: "from-lime-900 to-black" },
  { id: "h2", title: "Immaterial", artist: "SOPHIE", vibe: "hyperpop", familiarity: "familiar", energy: 5, mood: "euphoric", year: 2018, duration: "3:53", cover: "from-pink-900 to-fuchsia-950" },
  { id: "h3", title: "Pink Diamond", artist: "Charli xcx", vibe: "hyperpop", familiarity: "familiar", energy: 5, mood: "abrasive", year: 2020, duration: "2:04", cover: "from-rose-950 to-black" },
  { id: "h4", title: "Bunnies", artist: "Alice Longyu Gao", vibe: "hyperpop", familiarity: "new", energy: 4, mood: "erratic", year: 2021, duration: "2:15", cover: "from-yellow-950 to-pink-950" },
  { id: "h5", title: "Clueless", artist: "underscores", vibe: "hyperpop", familiarity: "new", energy: 4, mood: "infectious", year: 2023, duration: "3:08", cover: "from-emerald-900 to-cyan-950" },
  { id: "h6", title: "Star Quality", artist: "dltzk / Jane Remover", vibe: "hyperpop", familiarity: "new", energy: 5, mood: "maximal", year: 2021, duration: "3:42", cover: "from-indigo-900 to-violet-950" },

  // ── JAZZ ────────────────────────────────────────────────────────────
  { id: "j1", title: "So What", artist: "Miles Davis", vibe: "jazz", familiarity: "familiar", energy: 2, mood: "cool", year: 1959, duration: "9:22", cover: "from-blue-900 to-black" },
  { id: "j2", title: "Red Clay", artist: "Freddie Hubbard", vibe: "jazz", familiarity: "familiar", energy: 3, mood: "funky", year: 1970, duration: "12:11", cover: "from-orange-950 to-black" },
  { id: "j3", title: "Afro Blue", artist: "Robert Glasper ft. Erykah Badu", vibe: "jazz", familiarity: "familiar", energy: 3, mood: "sensual", year: 2012, duration: "5:13", cover: "from-purple-950 to-stone-900" },
  { id: "j4", title: "Pigs", artist: "Alfa Mist", vibe: "jazz", familiarity: "new", energy: 2, mood: "smoky", year: 2021, duration: "4:50", cover: "from-stone-900 to-neutral-950" },
  { id: "j5", title: "Koko", artist: "Mansur Brown", vibe: "jazz", familiarity: "new", energy: 3, mood: "electric", year: 2021, duration: "3:35", cover: "from-teal-900 to-black" },
  { id: "j6", title: "Lift Off", artist: "Tom Misch & Yussef Dayes", vibe: "jazz", familiarity: "new", energy: 4, mood: "fluid", year: 2020, duration: "4:49", cover: "from-amber-950 to-black" },

  // ── SHOEGAZE ────────────────────────────────────────────────────────
  { id: "s1", title: "When You Sleep", artist: "My Bloody Valentine", vibe: "shoegaze", familiarity: "familiar", energy: 4, mood: "blissful", year: 1991, duration: "4:11", cover: "from-pink-900 to-rose-950" },
  { id: "s2", title: "Alison", artist: "Slowdive", vibe: "shoegaze", familiarity: "familiar", energy: 3, mood: "drifting", year: 1993, duration: "3:51", cover: "from-indigo-950 to-black" },
  { id: "s3", title: "Vapour Trail", artist: "Ride", vibe: "shoegaze", familiarity: "familiar", energy: 3, mood: "melodic", year: 1990, duration: "4:18", cover: "from-sky-950 to-blue-900" },
  { id: "s4", title: "Deceiver", artist: "DIIV", vibe: "shoegaze", familiarity: "new", energy: 4, mood: "heavy", year: 2019, duration: "4:20", cover: "from-slate-900 to-black" },
  { id: "s5", title: "Kicking the Sun", artist: "They Are Gutting a Body of Water", vibe: "shoegaze", familiarity: "new", energy: 4, mood: "distorted", year: 2022, duration: "3:10", cover: "from-amber-900 to-zinc-950" },
  { id: "s6", title: "Fever Dream", artist: "Full Body 2", vibe: "shoegaze", familiarity: "new", energy: 5, mood: "digital haze", year: 2023, duration: "2:55", cover: "from-fuchsia-950 to-cyan-950" },
];
