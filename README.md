# Vicki — Billing Support Assistant

A single-page React app that helps clinic staff generate plain-English email responses explaining patient bills. Powered by Claude via the Anthropic API.

## Setup

### 1. Clone and install

```bash
# Install client dependencies
cd client && npm install

# Install server dependencies
cd ../server && npm install
```

### 2. Add your API key

Copy the example env file and add your Anthropic API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run

Open two terminals:

**Terminal 1 — API server (port 3001):**
```bash
cd server && npm run dev
```

**Terminal 2 — React client (port 5173):**
```bash
cd client && npm run dev
```

Then open `http://localhost:5173` in your browser.

## Demo Mode

Toggle "Demo Mode" in the top-right corner of the app. When on:
- Clicking a patient instantly shows a pre-written polished response, no API call needed.
- An orange "Demo" badge appears in the header.
- The generate button reads "Show demo response."

Toggle it off to use the live API.

## Features

- Patient inquiry list with color-coded scenario tags (Copay, Deductible, Denied, Coinsurance)
- Claim detail card with all billing fields
- Proportional breakdown bar chart
- AI-generated responses with four labeled sections
- Inline editing with a textarea before copying
- Copy button always copies the current (possibly edited) state as plain text

## Stack

- React 19 + Vite + Tailwind CSS v4
- Express 5 (API server)
- Anthropic Node SDK
