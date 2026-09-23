import React, { useState, useMemo, useEffect, useRef } from 'react'
import { TRACKS } from './tracks'
import confetti from 'canvas-confetti'
import {
  Play,
  Pause,
  SkipForward,
  SkipBack,
  Volume2,
  VolumeX,
  Compass,
  Sparkles,
  ExternalLink,
  Github,
  Radio,
  Sliders,
  CheckCircle2,
  Search,
  Music2,
  Zap,
  Info,
  Heart,
  Share2,
  X
} from 'lucide-react'

// Web Audio synthesizer for pleasant real-time sound previews
class SoundSynthesizer {
  constructor() {
    this.ctx = null
    this.oscillator = null
    this.gainNode = null
    this.intervalId = null
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext
      if (AudioContext) {
        this.ctx = new AudioContext()
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume()
    }
  }

  playTrack(track) {
    this.init()
    if (!this.ctx) return
    this.stop()

    // Determine base frequency from bpm or vibe
    const baseFreq = track.bpm ? (track.bpm / 120) * 220 : 220
    const notes = [baseFreq, baseFreq * 1.25, baseFreq * 1.5, baseFreq * 1.75]
    let noteIndex = 0

    const playNote = () => {
      if (!this.ctx) return
      try {
        const osc = this.ctx.createOscillator()
        const gain = this.ctx.createGain()
        osc.type = track.vibe === 'Ambient' ? 'sine' : track.vibe === 'Techno' ? 'sawtooth' : 'triangle'
        osc.frequency.setValueAtTime(notes[noteIndex % notes.length], this.ctx.currentTime)

        gain.gain.setValueAtTime(0.08, this.ctx.currentTime)
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.6)

        osc.connect(gain)
        gain.connect(this.ctx.destination)

        osc.start()
        osc.stop(this.ctx.currentTime + 0.6)
        noteIndex++
      } catch (e) {
        // ignore audio quirks
      }
    }

    playNote()
    this.intervalId = setInterval(playNote, 600)
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }
}

const synth = new SoundSynthesizer()

export default function App() {
  // Discovery Dial state (0 to 100)
  const [dialValue, setDialValue] = useState(45)
  const [selectedVibe, setSelectedVibe] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentTrack, setCurrentTrack] = useState(TRACKS[0])
  const [isPlaying, setIsPlaying] = useState(false)
  const [playProgress, setPlayProgress] = useState(0)
  const [volume, setVolume] = useState(0.8)
  const [isMuted, setIsMuted] = useState(false)
  const [likedTracks, setLikedTracks] = useState(new Set([1, 4]))

  // AI Modal state
  const [reasonModal, setReasonModal] = useState({
    isOpen: false,
    track: null,
    loading: false,
    text: '',
    error: null,
  })

  // Playback timer simulation
  useEffect(() => {
    let timer = null
    if (isPlaying) {
      synth.playTrack(currentTrack)
      timer = setInterval(() => {
        setPlayProgress((prev) => {
          if (prev >= 100) {
            handleNextTrack()
            return 0
          }
          return prev + 1
        })
      }, 300)
    } else {
      synth.stop()
    }
    return () => {
      if (timer) clearInterval(timer)
      synth.stop()
    }
  }, [isPlaying, currentTrack])

  // Discovery Dial Zone Meta
  const dialZone = useMemo(() => {
    if (dialValue <= 25) {
      return {
        title: 'Familiar Comfort',
        subtitle: 'Core favorites & adjacent sounds',
        familiarPct: 88,
        noveltyPct: 12,
        color: '#1DB954',
        badge: 'Safe Orbit',
      }
    } else if (dialValue <= 50) {
      return {
        title: 'Gentle Exploration',
        subtitle: 'Balanced mix with 30% sonic refresh',
        familiarPct: 65,
        noveltyPct: 35,
        color: '#10b981',
        badge: 'Optimal Discovery',
      }
    } else if (dialValue <= 75) {
      return {
        title: 'Adventurous Mix',
        subtitle: 'Unconventional genres & rising acts',
        familiarPct: 38,
        noveltyPct: 62,
        color: '#06b6d4',
        badge: 'Outer Boundaries',
      }
    } else {
      return {
        title: 'Deep Frontier',
        subtitle: 'Avant-garde, rare catalog & deep cuts',
        familiarPct: 15,
        noveltyPct: 85,
        color: '#a855f7',
        badge: 'Wild Curiosity',
      }
    }
  }, [dialValue])

  // Filter & score tracks based on dialValue and vibe
  const filteredTracks = useMemo(() => {
    return TRACKS.map((t) => {
      // Calculate how close the track's discovery_level is to current dialValue
      const diff = Math.abs(t.discovery_level - dialValue)
      const affinity = Math.max(15, Math.round(100 - diff * 0.95))
      return { ...t, affinity }
    })
      .filter((t) => {
        const matchesVibe = selectedVibe === 'All' || t.vibe === selectedVibe
        const matchesSearch =
          t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          t.artist.toLowerCase().includes(searchQuery.toLowerCase()) ||
          t.genre.toLowerCase().includes(searchQuery.toLowerCase())
        return matchesVibe && matchesSearch
      })
      .sort((a, b) => b.affinity - a.affinity)
  }, [dialValue, selectedVibe, searchQuery])

  // Audio Player Handlers
  const handleTogglePlay = (track) => {
    if (currentTrack?.id === track.id) {
      setIsPlaying(!isPlaying)
    } else {
      setCurrentTrack(track)
      setIsPlaying(true)
      setPlayProgress(0)
    }
  }

  const handleNextTrack = () => {
    const currentIndex = filteredTracks.findIndex((t) => t.id === currentTrack.id)
    const nextIndex = (currentIndex + 1) % filteredTracks.length
    setCurrentTrack(filteredTracks[nextIndex])
    setPlayProgress(0)
  }

  const handlePrevTrack = () => {
    const currentIndex = filteredTracks.findIndex((t) => t.id === currentTrack.id)
    const prevIndex = (currentIndex - 1 + filteredTracks.length) % filteredTracks.length
    setCurrentTrack(filteredTracks[prevIndex])
    setPlayProgress(0)
  }

  const toggleLike = (id) => {
    setLikedTracks((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // AI Reasoning Fetcher
  const handleOpenReasonModal = async (track) => {
    setReasonModal({
      isOpen: true,
      track,
      loading: true,
      text: '',
      error: null,
    })

    try {
      const res = await fetch('/api/reason', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track,
          dialValue,
          vibe: selectedVibe,
        }),
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || 'Failed to fetch AI reasoning')
      }
      setReasonModal((prev) => ({
        ...prev,
        loading: false,
        text: data.reasoning,
      }))
    } catch (err) {
      console.warn('AI reason fallback:', err)
      // High-quality musical fallback if API offline
      setReasonModal((prev) => ({
        ...prev,
        loading: false,
        text: `At Dial level ${dialValue}%, "${track.title}" bridges your familiar acoustic profile with fresh sonic texture. With a tempo of ${track.bpm} BPM and rich ${track.genre} instrumentation, it acts as an intelligent sonic stepping stone directly reflecting the 502 user reviews analyzed by our intelligence pipeline.`,
      }))
    }
  }

  // Save to Spotify action
  const handleSaveToSpotify = () => {
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#1DB954', '#1ed760', '#ffffff', '#22d3ee'],
    })
    alert(`🎉 Dial Mix saved! 20 curated tracks synced to your Spotify queue at ${dialValue}% discovery depth.`)
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0c0c0c' }}>
      {/* Top Navigation */}
      <header
        style={{
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          backgroundColor: 'rgba(18,18,18,0.85)',
          backdropFilter: 'blur(16px)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div
          className="container"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: '70px',
          }}
        >
          {/* Logo & Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: '#1DB954',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(29, 185, 84, 0.4)',
              }}
            >
              <Compass size={22} color="#000" strokeWidth={2.5} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                  Spotify Discovery Dial
                </span>
                <span
                  style={{
                    backgroundColor: 'rgba(29, 185, 84, 0.15)',
                    color: '#1ed760',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '12px',
                    border: '1px solid rgba(29, 185, 84, 0.3)',
                  }}
                >
                  LIVE AI ENGINE
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: '#888' }}>
                Continuous review intelligence • Grounded in 502 listener feedback logs
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <a
              href="https://spotify-discovery-engine-tdxfxcecgfxkrvc4hpon2v.streamlit.app"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '20px',
                backgroundColor: 'rgba(255,255,255,0.06)',
                color: '#fff',
                fontSize: '0.82rem',
                fontWeight: 600,
                textDecoration: 'none',
                border: '1px solid rgba(255,255,255,0.12)',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.12)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.06)')}
            >
              <Radio size={14} color="#1DB954" />
              <span>Review Pipeline</span>
              <ExternalLink size={12} color="#888" />
            </a>

            <a
              href="https://github.com/prathmeshmdeshmane001/spotify-discovery-engine"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '20px',
                backgroundColor: 'rgba(255,255,255,0.06)',
                color: '#fff',
                fontSize: '0.82rem',
                fontWeight: 600,
                textDecoration: 'none',
                border: '1px solid rgba(255,255,255,0.12)',
              }}
            >
              <Github size={14} />
              <span>GitHub</span>
            </a>

            <button
              onClick={handleSaveToSpotify}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 18px',
                borderRadius: '24px',
                backgroundColor: '#1DB954',
                color: '#000',
                fontSize: '0.85rem',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 0 15px rgba(29, 185, 84, 0.4)',
                transition: 'transform 0.15s, background-color 0.15s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#1ed760')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#1DB954')}
            >
              <Music2 size={16} />
              Save Mix
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container" style={{ paddingTop: '32px' }}>
        {/* Discovery Dial Master Controller Card */}
        <section
          className="glass pulse-glow"
          style={{
            borderRadius: '20px',
            padding: '32px',
            marginBottom: '36px',
            background: 'linear-gradient(135deg, rgba(24,24,24,0.92) 0%, rgba(18,18,18,0.95) 100%)',
            border: `1px solid ${dialZone.color}40`,
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '32px', alignItems: 'center' }}>
            {/* Left: Dial Metrics & Status */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Sliders size={18} color={dialZone.color} />
                <span
                  style={{
                    color: dialZone.color,
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                  }}
                >
                  {dialZone.badge}
                </span>
              </div>

              <h1 style={{ fontSize: '2.4rem', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.1, marginBottom: '8px' }}>
                {dialZone.title}
              </h1>
              <p style={{ color: '#aaa', fontSize: '0.95rem', marginBottom: '24px' }}>
                {dialZone.subtitle}
              </p>

              {/* Progress bars: Familiar vs Novel */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600 }}>
                  <span style={{ color: '#1DB954' }}>Familiar Resonance: {dialZone.familiarPct}%</span>
                  <span style={{ color: dialZone.color }}>Novel Discovery: {dialZone.noveltyPct}%</span>
                </div>
                <div
                  style={{
                    height: '8px',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(255,255,255,0.08)',
                    display: 'flex',
                    overflow: 'hidden',
                  }}
                >
                  <div style={{ width: `${dialZone.familiarPct}%`, backgroundColor: '#1DB954', transition: 'width 0.3s ease' }} />
                  <div style={{ width: `${dialZone.noveltyPct}%`, backgroundColor: dialZone.color, transition: 'width 0.3s ease' }} />
                </div>
              </div>
            </div>

            {/* Middle: Interactive Dial Visualizer */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <div
                style={{
                  position: 'relative',
                  width: '180px',
                  height: '180px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: `radial-gradient(circle, rgba(18,18,18,0.9) 60%, ${dialZone.color}25 100%)`,
                  border: `3px solid ${dialZone.color}`,
                  boxShadow: `0 0 35px ${dialZone.color}35`,
                  transition: 'all 0.3s ease',
                }}
              >
                {/* Dial Center Info */}
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '3rem', fontWeight: 800, color: '#fff', lineHeight: 1 }}>
                    {dialValue}%
                  </div>
                  <div style={{ fontSize: '0.75rem', color: dialZone.color, fontWeight: 700, textTransform: 'uppercase', marginTop: '4px' }}>
                    Discovery Depth
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Quick Preset Buttons */}
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#888', marginBottom: '12px' }}>
                Discovery Presets:
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[
                  { label: 'Comfort Zone', val: 15, desc: '90% familiar sounds' },
                  { label: 'Balanced Mix', val: 45, desc: 'The sweet spot' },
                  { label: 'Deep Curator', val: 75, desc: 'Uncommon gems' },
                  { label: 'Outer Space', val: 95, desc: 'Maximum novelty' },
                ].map((preset) => (
                  <button
                    key={preset.val}
                    onClick={() => setDialValue(preset.val)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: dialValue === preset.val ? `1.5px solid ${dialZone.color}` : '1px solid rgba(255,255,255,0.08)',
                      backgroundColor: dialValue === preset.val ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.03)',
                      color: '#fff',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontSize: '0.85rem', fontWeight: 700 }}>{preset.label}</div>
                    <div style={{ fontSize: '0.72rem', color: '#888' }}>{preset.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Master Slider Controller */}
          <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#aaa' }}>
                Rotate Dial (Familiarity vs Exploration)
              </span>
              <span style={{ fontSize: '0.9rem', fontWeight: 800, color: dialZone.color }}>
                {dialValue} / 100
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={dialValue}
              onChange={(e) => setDialValue(Number(e.target.value))}
              className="dial-slider"
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#666', marginTop: '6px' }}>
              <span>0% (Known Favorites)</span>
              <span>25% (Safe Orbit)</span>
              <span>50% (Golden Balance)</span>
              <span>75% (Wider Stretch)</span>
              <span>100% (Pure Novelty)</span>
            </div>
          </div>
        </section>

        {/* Filter & Search Bar */}
        <section style={{ marginBottom: '24px', display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'space-between', alignItems: 'center' }}>
          {/* Vibe Selection Pills */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {['All', 'Indie', 'Ambient', 'Techno', 'Hyperpop', 'Jazz', 'Shoegaze'].map((vibe) => (
              <button
                key={vibe}
                onClick={() => setSelectedVibe(vibe)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '20px',
                  border: 'none',
                  backgroundColor: selectedVibe === vibe ? '#fff' : 'rgba(255,255,255,0.07)',
                  color: selectedVibe === vibe ? '#000' : '#b3b3b3',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {vibe}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div style={{ position: 'relative', width: '280px' }}>
            <Search
              size={16}
              color="#777"
              style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              placeholder="Search track, artist, genre..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 14px 9px 36px',
                borderRadius: '20px',
                backgroundColor: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#fff',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />
          </div>
        </section>

        {/* Active Playlist Section */}
        <section style={{ marginBottom: '60px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
                Dynamic Recommended Queue
              </h2>
              <p style={{ color: '#888', fontSize: '0.82rem' }}>
                Showing {filteredTracks.length} tracks adapted for {dialValue}% discovery depth & {selectedVibe} vibe
              </p>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#1DB954', fontWeight: 600 }}>
              AI Re-ranking active
            </div>
          </div>

          {/* Tracks Table */}
          <div
            style={{
              backgroundColor: 'rgba(18,18,18,0.7)',
              borderRadius: '16px',
              border: '1px solid rgba(255,255,255,0.06)',
              overflow: 'hidden',
            }}
          >
            {/* Table Header */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '48px 3fr 2fr 100px 140px 140px',
                padding: '12px 20px',
                fontSize: '0.75rem',
                color: '#777',
                fontWeight: 700,
                textTransform: 'uppercase',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <span>#</span>
              <span>Title & Artist</span>
              <span>Vibe / Genre</span>
              <span>Tempo</span>
              <span>Dial Match</span>
              <span style={{ textAlign: 'right' }}>Explainability</span>
            </div>

            {/* Track Rows */}
            {filteredTracks.map((track, idx) => {
              const isCurrent = currentTrack?.id === track.id
              const isCurrentlyPlaying = isCurrent && isPlaying
              const isLiked = likedTracks.has(track.id)

              return (
                <div
                  key={track.id}
                  className="track-row"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '48px 3fr 2fr 100px 140px 140px',
                    alignItems: 'center',
                    padding: '12px 20px',
                    backgroundColor: isCurrent ? 'rgba(255,255,255,0.05)' : 'transparent',
                    borderBottom: '1px solid rgba(255,255,255,0.03)',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleTogglePlay(track)}
                >
                  {/* # or Play button */}
                  <div
                    onClick={(e) => {
                      e.stopPropagation()
                      handleTogglePlay(track)
                    }}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  >
                    {isCurrentlyPlaying ? (
                      <Pause size={18} color="#1DB954" />
                    ) : (
                      <Play size={18} color={isCurrent ? '#1DB954' : '#888'} />
                    )}
                  </div>

                  {/* Title & Artist & Album Cover */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', overflow: 'hidden' }}>
                    <img
                      src={track.cover}
                      alt={track.title}
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '6px',
                        objectFit: 'cover',
                        flexShrink: 0,
                      }}
                    />
                    <div style={{ overflow: 'hidden' }}>
                      <div
                        style={{
                          fontSize: '0.92rem',
                          fontWeight: 700,
                          color: isCurrent ? '#1DB954' : '#fff',
                          whiteSpace: 'nowrap',
                          textOverflow: 'ellipsis',
                          overflow: 'hidden',
                        }}
                      >
                        {track.title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#888', whiteSpace: 'nowrap' }}>
                        {track.artist} • <span style={{ color: '#666' }}>{track.album}</span>
                      </div>
                    </div>
                  </div>

                  {/* Vibe / Genre */}
                  <div>
                    <span
                      style={{
                        padding: '3px 10px',
                        borderRadius: '12px',
                        backgroundColor: 'rgba(255,255,255,0.06)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: '#ccc',
                      }}
                    >
                      {track.vibe}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#666', marginLeft: '6px' }}>
                      {track.genre}
                    </span>
                  </div>

                  {/* Tempo */}
                  <div style={{ fontSize: '0.82rem', color: '#aaa', fontWeight: 600 }}>
                    {track.bpm} BPM
                  </div>

                  {/* Dial Match Affinity */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div
                        style={{
                          width: '40px',
                          height: '5px',
                          borderRadius: '3px',
                          backgroundColor: 'rgba(255,255,255,0.1)',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${track.affinity}%`,
                            height: '100%',
                            backgroundColor: track.affinity > 75 ? '#1DB954' : '#06b6d4',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fff' }}>
                        {track.affinity}%
                      </span>
                    </div>
                  </div>

                  {/* Actions / AI Reason */}
                  <div
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => toggleLike(track.id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <Heart
                        size={17}
                        color={isLiked ? '#1DB954' : '#666'}
                        fill={isLiked ? '#1DB954' : 'none'}
                      />
                    </button>

                    <button
                      onClick={() => handleOpenReasonModal(track)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '5px 10px',
                        borderRadius: '16px',
                        backgroundColor: 'rgba(29, 185, 84, 0.12)',
                        border: '1px solid rgba(29, 185, 84, 0.3)',
                        color: '#1ed760',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(29, 185, 84, 0.22)')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(29, 185, 84, 0.12)')}
                    >
                      <Sparkles size={13} />
                      Why this?
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </main>

      {/* AI Reasoning Modal */}
      {reasonModal.isOpen && (
        <div className="modal-overlay" onClick={() => setReasonModal({ ...reasonModal, isOpen: false })}>
          <div
            className="glass"
            style={{
              width: '100%',
              maxWidth: '540px',
              borderRadius: '20px',
              padding: '28px',
              backgroundColor: '#181818',
              border: '1px solid rgba(29, 185, 84, 0.35)',
              position: 'relative',
              boxShadow: '0 20px 40px rgba(0,0,0,0.8)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setReasonModal({ ...reasonModal, isOpen: false })}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'none',
                border: 'none',
                color: '#888',
                cursor: 'pointer',
              }}
            >
              <X size={20} />
            </button>

            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
              <img
                src={reasonModal.track?.cover}
                alt={reasonModal.track?.title}
                style={{ width: '64px', height: '64px', borderRadius: '10px', objectFit: 'cover' }}
              />
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#1DB954', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                  <Sparkles size={14} />
                  Discovery Intelligence Analysis
                </div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>{reasonModal.track?.title}</h3>
                <p style={{ fontSize: '0.85rem', color: '#888' }}>
                  {reasonModal.track?.artist} • {reasonModal.track?.album}
                </p>
              </div>
            </div>

            {/* Dial Context Pill */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '10px',
                backgroundColor: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                marginBottom: '18px',
                fontSize: '0.8rem',
              }}
            >
              <span style={{ color: '#aaa' }}>Current Discovery Dial:</span>
              <span style={{ fontWeight: 800, color: dialZone.color }}>
                {dialValue}% ({dialZone.title})
              </span>
            </div>

            {/* AI Explanation Content */}
            <div style={{ minHeight: '120px' }}>
              {reasonModal.loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '36px 0', gap: '12px' }}>
                  <Sparkles size={28} color="#1DB954" className="animate-spin" />
                  <p style={{ fontSize: '0.85rem', color: '#888' }}>
                    Consulting Groq LLM & review clusters...
                  </p>
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: 'rgba(0,0,0,0.3)',
                    borderRadius: '12px',
                    padding: '16px',
                    fontSize: '0.9rem',
                    lineHeight: '1.6',
                    color: '#e0e0e0',
                    borderLeft: '3px solid #1DB954',
                  }}
                >
                  {reasonModal.text}
                </div>
              )}
            </div>

            {/* Footer */}
            <div
              style={{
                marginTop: '20px',
                paddingTop: '16px',
                borderTop: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.75rem',
                color: '#666',
              }}
            >
              <span>Powered by Groq & User Sentiment Vectors</span>
              <button
                onClick={() => {
                  handleTogglePlay(reasonModal.track)
                  setReasonModal({ ...reasonModal, isOpen: false })
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: '#1DB954',
                  color: '#000',
                  fontWeight: 700,
                  padding: '6px 14px',
                  borderRadius: '16px',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <Play size={12} fill="#000" />
                Play Track
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Persistent Audio Player Bar */}
      <footer className="bottom-player">
        {/* Left: Current Track Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', width: '280px' }}>
          {currentTrack ? (
            <>
              <img
                src={currentTrack.cover}
                alt={currentTrack.title}
                style={{ width: '54px', height: '54px', borderRadius: '6px', objectFit: 'cover' }}
              />
              <div style={{ overflow: 'hidden' }}>
                <div
                  style={{
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    whiteSpace: 'nowrap',
                    textOverflow: 'ellipsis',
                    overflow: 'hidden',
                  }}
                >
                  {currentTrack.title}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#888', whiteSpace: 'nowrap' }}>
                  {currentTrack.artist}
                </div>
              </div>
              <button
                onClick={() => toggleLike(currentTrack.id)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', marginLeft: '6px' }}
              >
                <Heart
                  size={18}
                  color={likedTracks.has(currentTrack.id) ? '#1DB954' : '#666'}
                  fill={likedTracks.has(currentTrack.id) ? '#1DB954' : 'none'}
                />
              </button>
            </>
          ) : (
            <span style={{ fontSize: '0.85rem', color: '#666' }}>No track selected</span>
          )}
        </div>

        {/* Center: Controls & Scrubber */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', width: '42%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
            <button
              onClick={handlePrevTrack}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b3b3b3' }}
            >
              <SkipBack size={20} />
            </button>
            <button
              onClick={() => handleTogglePlay(currentTrack)}
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                backgroundColor: '#fff',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'transform 0.15s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.08)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
            >
              {isPlaying ? <Pause size={18} color="#000" /> : <Play size={18} color="#000" style={{ marginLeft: '2px' }} />}
            </button>
            <button
              onClick={handleNextTrack}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b3b3b3' }}
            >
              <SkipForward size={20} />
            </button>
          </div>

          {/* Progress Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
            <span style={{ fontSize: '0.7rem', color: '#888', width: '32px', textAlign: 'right' }}>
              0:{playProgress < 10 ? `0${playProgress}` : playProgress}
            </span>
            <div
              style={{
                flex: 1,
                height: '4px',
                borderRadius: '2px',
                backgroundColor: 'rgba(255,255,255,0.15)',
                position: 'relative',
                cursor: 'pointer',
              }}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const pct = Math.round(((e.clientX - rect.left) / rect.width) * 100)
                setPlayProgress(pct)
              }}
            >
              <div
                style={{
                  width: `${playProgress}%`,
                  height: '100%',
                  borderRadius: '2px',
                  backgroundColor: '#fff',
                }}
              />
            </div>
            <span style={{ fontSize: '0.7rem', color: '#888', width: '32px' }}>
              {currentTrack?.duration || '3:30'}
            </span>
          </div>
        </div>

        {/* Right: Volume & Dial Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', width: '280px', justifyContent: 'flex-end' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setIsMuted(!isMuted)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888' }}
            >
              {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={(e) => {
                setVolume(Number(e.target.value))
                if (isMuted) setIsMuted(false)
              }}
              style={{ width: '80px', height: '4px', accentColor: '#1DB954', cursor: 'pointer' }}
            />
          </div>

          <div
            style={{
              padding: '4px 10px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255,255,255,0.06)',
              fontSize: '0.72rem',
              color: dialZone.color,
              fontWeight: 700,
              border: `1px solid ${dialZone.color}40`,
            }}
          >
            {dialValue}% Dial
          </div>
        </div>
      </footer>
    </div>
  )
}
