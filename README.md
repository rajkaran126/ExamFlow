# EXAMFLOW – Frontend, Design System & User Experience

**Project:** AI-056  
**Problem Statement:** PS-072 – Online Exam Proctoring Result Engine with Negative Marking, Sectional Cut-offs and Shift Normalisation.  
**Role:** Senior Frontend Architect & UI/UX Engineer (Team Member 1)

---

## Overview

EXAMFLOW is a production-oriented examination operations platform featuring:
- **Cinematic Landing Page:** Full-screen video background with requestAnimationFrame-based opacity fade in/out cycle.
- **Liquid-Glass Design System:** Custom CSS tokenized design system with translucent backdrops, border highlights, and dark/light elevations.
- **15 Themes with WCAG AA Contrast:** Light, Dark, System, High Contrast, Retro/Vintage, Minimalist, Nature/Earthy, Solarized Dark, Nordic Frost, Midnight Ocean, Roohafza, Minecraft, Terminal, and Krik Party.
- **Evaluation & Normalisation UI:** Pure presentation of backend-computed raw scores, negative marking deductions, sectional cut-offs, proctoring penalties, and multi-shift normalisation statistics without duplicated business logic.
- **Proctoring Engine Hub:** Anomaly logs, severity tags, audio-visual penalty allocations, and disqualification status flags.
- **EXAMFLOW AI Copilot:** Floating assistant launcher, expandable drawer, PDF rulebook upload, streaming simulation, voice controls, and quick copy.
- **Fully Typed API Client:** Centralized HTTP abstraction with error handling, authentication tokens, and typed responses.

---

## Technology Stack

- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** TypeScript 5+
- **Styling:** Tailwind CSS, Liquid-Glass CSS variable tokens
- **Icons:** lucide-react
- **Testing:** Vitest, Testing Library, JSDOM

---

## Setup & Local Development

### 1. Prerequisites
- Node.js 18+ (tested on Node 26)
- npm

### 2. Installation
```bash
git clone <repo-url>
cd EXAMFLOW
npm install
```

### 3. Environment Variables
Create a `.env` file in the project root:
```env
VITE_API_BASE_URL=http://localhost:3000/api
```

### 4. Running the Development Server
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

### 5. Running Tests
```bash
npm run test
```

### 6. Production Build
```bash
npm run build
npm run preview
```

---

## Deployment Instructions

### Static Site Hosting (Vercel / Netlify / Cloudflare Pages / AWS S3 + CloudFront)
1. Run `npm run build` to generate the production bundle inside `dist/`.
2. Configure SPA fallback routing to direct all non-asset requests to `index.html`.
3. Set `VITE_API_BASE_URL` to point to Team Member 2's backend service.
