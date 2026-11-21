// ============================================================
// EXAMFLOW – Cinematic Landing Page
// ============================================================

import { useRef, useEffect, useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ChevronDown,
  LayoutDashboard,
  ClipboardList,
  Users,
  Award,
  LogIn,
} from 'lucide-react';

const VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4';

export default function LandingPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const rafRef = useRef<number | null>(null);
  const [navOpen, setNavOpen] = useState(false);

  // ── RAF-based opacity animation ────────────────────────
  const animateOpacity = useCallback(() => {
    // Cancel any pending frame
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }

    const video = videoRef.current;
    if (!video) return;

    const FADE_IN_DURATION = 0.5;    // 500ms
    const FADE_OUT_BEFORE_END = 0.55; // Start fading 0.55s before end
    const FPS_60 = 1000 / 60;

    let lastTime = performance.now();

    const tick = (now: number) => {
      const delta = (now - lastTime) / 1000; // seconds
      lastTime = now;

      if (!video || video.paused) return;

      const currentTime = video.currentTime;
      const duration = video.duration;

      if (!duration || isNaN(duration)) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      let targetOpacity: number;
      const timeRemaining = duration - currentTime;

      if (currentTime < FADE_IN_DURATION) {
        // Fade in
        targetOpacity = currentTime / FADE_IN_DURATION;
      } else if (timeRemaining <= FADE_OUT_BEFORE_END) {
        // Fade out
        targetOpacity = timeRemaining / FADE_OUT_BEFORE_END;
      } else {
        targetOpacity = 1;
      }

      // Clamp
      targetOpacity = Math.max(0, Math.min(1, targetOpacity));

      // Smooth step from current opacity
      const currentOpacity = parseFloat(video.style.opacity || '0');
      const speed = 4; // approach speed
      const newOpacity =
        currentOpacity + (targetOpacity - currentOpacity) * Math.min(delta * speed, 1);

      video.style.opacity = String(Math.max(0, Math.min(1, newOpacity)));

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.style.opacity = '0';

    const handlePlay = () => animateOpacity();
    const handleEnded = () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      video.style.opacity = '0';
      video.currentTime = 0;
      video.play().catch(() => {});
    };

    video.addEventListener('play', handlePlay);
    video.addEventListener('ended', handleEnded);

    // Autoplay
    video.play().catch(() => {});

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('ended', handleEnded);
    };
  }, [animateOpacity]);

  return (
    <div className="min-h-screen bg-black overflow-hidden relative">
      {/* ── Background Video ─────────────────────────────── */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover translate-y-[17%]"
        src={VIDEO_URL}
        muted
        playsInline
        preload="auto"
        style={{ opacity: 0 }}
        aria-hidden="true"
      />

      {/* ── Overlay ──────────────────────────────────────── */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/30 to-black/70" />

      {/* ── Navigation ───────────────────────────────────── */}
      <nav className="relative z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="h-10 w-10 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center text-white font-bold text-lg group-hover:bg-white/20 transition-colors">
                EF
              </div>
              <span className="font-display text-2xl text-white tracking-tight">
                EXAMFLOW
              </span>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-8">
              {[
                { label: 'Dashboard', href: '/app', icon: LayoutDashboard },
                { label: 'Examinations', href: '/app/examinations', icon: ClipboardList },
                { label: 'Candidates', href: '/app/candidates', icon: Users },
                { label: 'Results', href: '/app/results', icon: Award },
              ].map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  className="text-white/70 hover:text-white text-sm font-medium transition-colors flex items-center gap-1.5"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              ))}
              <Link
                to="/login"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/20 text-white text-sm font-medium hover:bg-white/20 transition-colors"
              >
                <LogIn className="h-4 w-4" />
                Login
              </Link>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 text-white"
              onClick={() => setNavOpen(!navOpen)}
              aria-label="Toggle navigation"
            >
              {navOpen ? (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>

          {/* Mobile Nav */}
          {navOpen && (
            <div className="md:hidden pb-4 space-y-2">
              {[
                { label: 'Dashboard', href: '/app' },
                { label: 'Examinations', href: '/app/examinations' },
                { label: 'Candidates', href: '/app/candidates' },
                { label: 'Results', href: '/app/results' },
                { label: 'Login', href: '/login' },
              ].map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  className="block px-4 py-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg text-sm"
                  onClick={() => setNavOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          )}
        </div>
      </nav>

      {/* ── Hero Content ─────────────────────────────────── */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-5rem)]">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="font-display text-6xl sm:text-7xl lg:text-8xl text-white mb-6 leading-tight">
            EXAMFLOW
          </h1>

          <p className="text-xl sm:text-2xl text-white/80 font-light italic mb-4 font-display">
            "Every answer. Every rule. Every result."
          </p>

          <p className="text-base sm:text-lg text-white/60 max-w-2xl mx-auto mb-12 leading-relaxed">
            An intelligent examination operations platform for accurate evaluation,
            transparent results and smarter examination management.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/app"
              className="group flex items-center gap-3 px-8 py-4 rounded-xl bg-white text-black font-semibold text-lg hover:bg-white/90 transition-all shadow-lg shadow-white/10"
            >
              Open Examination Workspace
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/app/evaluation"
              className="flex items-center gap-3 px-8 py-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-white font-semibold text-lg hover:bg-white/20 transition-all"
            >
              Explore Evaluation Workflow
            </Link>
          </div>
        </div>
      </div>

      {/* ── Scroll indicator ─────────────────────────────── */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 animate-bounce">
        <ChevronDown className="h-6 w-6 text-white/40" />
      </div>
    </div>
  );
}
