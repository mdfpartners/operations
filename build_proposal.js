const PptxGenJS = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const NAVY   = '0D1F3C';
const WHITE  = 'FFFFFF';
const MGRAY  = '6B7280';
const LGRAY  = '9CA3AF';
const RULE   = 'D1D5DB';
const GOLD   = 'C9A84C';
const PROSPECT = '1B3A6B';  // LSI brand - deep blue (no distinct color extracted, using default)
const GREEN  = '2E7D52';
const DKGRAY = '374151';

const SLIDE_W = 10;  // inches
const SLIDE_H = 5.625;

// ─── HELPERS ──────────────────────────────────────────────────────────────────
function toB64(filePath) {
  return fs.readFileSync(filePath).toString('base64');
}

function addContentChrome(slide, prs, pageNum, overline) {
  // Top navy rule
  slide.addShape(prs.ShapeType.rect, { x: 0, y: 0, w: SLIDE_W, h: 0.04, fill: { color: NAVY }, line: { color: NAVY } });
  // Overline
  if (overline) {
    slide.addText(overline, { x: 0.5, y: 0.10, w: 8, h: 0.18, fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5 });
  }
  // Page number
  slide.addText(String(pageNum), { x: 9.6, y: 0.08, w: 0.3, h: 0.18, fontSize: 8, color: LGRAY, fontFace: 'Calibri', align: 'right' });
  // MDF logo bottom right
  slide.addImage({ path: './mdf_logo_white_bg.png', x: 8.75, y: 5.15, w: 1.1, h: 0.65 });
}

function hairline(slide, x, y, w, color) {
  slide.addShape('rect', { x, y, w, h: 0.018, fill: { color: color || RULE }, line: { color: color || RULE } });
}

function vline(slide, x, y, h, color) {
  slide.addShape('rect', { x, y, w: 0.018, h, fill: { color: color || RULE }, line: { color: color || RULE } });
}

// ─── BUILD ────────────────────────────────────────────────────────────────────
async function buildProposal() {
  const prs = new PptxGenJS();
  prs.layout = 'LAYOUT_WIDE';
  prs.title = 'MDF Facility Services Proposal — Logical Systems';

  // ── SLIDE 1: COVER ──────────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    // Full-bleed background
    s.addImage({ path: './cover_photo.jpg', x: 0, y: 0, w: SLIDE_W, h: SLIDE_H });

    // MDF logo top-left (transparent)
    s.addImage({ path: './mdf_logo_transparent.png', x: 0.35, y: 0.28, w: 1.05, h: 0.62 });

    // "PREPARED FOR" micro-label
    s.addText('PREPARED FOR', {
      x: 0.5, y: 3.70, w: 6, h: 0.18,
      fontSize: 7, bold: true, color: 'A8B8CC', fontFace: 'Calibri', charSpacing: 3.5
    });

    // Prospect name
    s.addText('Logical Systems Inc.', {
      x: 0.5, y: 3.90, w: 7.5, h: 0.85,
      fontSize: 34, bold: true, color: WHITE, fontFace: 'Trebuchet MS'
    });

    // Hairline between name and metadata
    s.addShape('rect', { x: 0.5, y: 4.72, w: 6.5, h: 0.018, fill: { color: '5A6A7A' }, line: { color: '5A6A7A' } });

    // Metadata line
    s.addText('Facility Services Proposal  ·  April Bocox, Health and Safety Coordinator  ·  May 28, 2026', {
      x: 0.5, y: 4.76, w: 8.5, h: 0.22,
      fontSize: 9, color: '8B9BAD', fontFace: 'Calibri'
    });
  }

  // ── SLIDE 2: WHY MDF ────────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 2, 'WHY MAD DOG FACILITY PARTNERS');

    s.addText('You can choose any janitorial company.', {
      x: 0.5, y: 0.30, w: 9, h: 0.42, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Here is why our clients stay for an average of 6 years.', {
      x: 0.5, y: 0.72, w: 9, h: 0.24, fontSize: 11, color: MGRAY, fontFace: 'Calibri'
    });

    hairline(s, 0.5, 1.02, 9.0);

    // Three columns
    const cols = [
      {
        x: 0.5, stat: '92%+', label: 'avg. inspection score', title: 'Real-Time Quality Assurance',
        body: 'Every service is tracked through OrangeQC — a third-party inspection platform. You see the results. We see accountability.'
      },
      {
        x: 3.65, stat: '<24hr', label: 'avg. resolution time', title: 'Documented Service Resolution',
        body: 'Every issue generates a service ticket with a timestamp. Nothing falls through the cracks and nothing goes unaddressed.'
      },
      {
        x: 6.82, stat: 'CEO', label: 'is your primary contact', title: 'Direct Executive Access',
        body: 'Hereford Johnson, our CEO and US Air Force veteran, is reachable directly. No account managers, no call centers.'
      }
    ];

    cols.forEach((c, i) => {
      if (i > 0) vline(s, c.x - 0.17, 1.06, 3.6);
      // Stat
      s.addText(c.stat, { x: c.x, y: 1.12, w: 2.8, h: 0.72, fontSize: 40, bold: true, color: NAVY, fontFace: 'Trebuchet MS' });
      // Label
      s.addText(c.label, { x: c.x, y: 1.80, w: 2.8, h: 0.22, fontSize: 9, color: LGRAY, fontFace: 'Calibri' });
      hairline(s, c.x, 2.06, 2.8);
      // Title
      s.addText(c.title, { x: c.x, y: 2.14, w: 2.8, h: 0.30, fontSize: 12, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      // Body
      s.addText(c.body, { x: c.x, y: 2.48, w: 2.8, h: 0.90, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true });
    });

    // Pull quote
    hairline(s, 0.5, 4.62, 9.0);
    s.addText('"We surveyed our clients on what we should do more of. The #1 answer was communication and integrity. We believe this is why our average client has been with us for 6 years."', {
      x: 0.5, y: 4.68, w: 8.5, h: 0.40, fontSize: 10, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
  }

  // ── SLIDE 3: WE UNDERSTAND YOUR FACILITY ────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 3, 'YOUR FACILITY');

    s.addText('We built this for Logical Systems.', {
      x: 0.5, y: 0.30, w: 5.3, h: 0.52, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hairline(s, 0.5, 0.88, 5.3);

    s.addText(
      'LSI operates manufacturing and industrial facilities where precision, compliance, and uptime are non-negotiable. ' +
      'Your environment demands cleaning that works around production schedules, respects sensitive equipment, and meets the documentation standards your clients expect. ' +
      'MDF delivers compliance-ready facility services purpose-built for automation and controls environments — so your team stays focused on what they do best.',
      { x: 0.5, y: 0.98, w: 5.3, h: 1.40, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true }
    );

    vline(s, 5.98, 0.28, 4.6);

    // Right column fact rows
    const facts = [
      { stat: 'Manufacturing / Automation', label: 'Industry' },
      { stat: '~50,000 sq ft', label: 'Estimated Facility Scale' },
      { stat: 'OSHA / Production-Grade', label: 'Compliance Context' }
    ];

    facts.forEach((f, i) => {
      const y = 0.55 + i * 1.30;
      s.addText(f.label, { x: 6.2, y, w: 3.4, h: 0.20, fontSize: 8.5, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 2 });
      s.addText(f.stat, { x: 6.2, y: y + 0.22, w: 3.4, h: 0.36, fontSize: 16, bold: true, color: NAVY, fontFace: 'Trebuchet MS' });
      if (i < facts.length - 1) hairline(s, 6.2, y + 0.65, 3.4);
    });
  }

  // ── SLIDE 4: SCOPE OF WORK ───────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 4, 'SCOPE OF WORK');

    s.addText('Your Facility. Your Scope.', {
      x: 0.5, y: 0.30, w: 9, h: 0.42, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Weekly · Start July 1, 2026  ·  Month-to-Month Contract', {
      x: 0.5, y: 0.70, w: 9, h: 0.24, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.00, 9.0);

    // Zone definitions from intake form
    const zones = [
      { name: 'Offices & Common Areas', tasks: 'General dusting (weekly), front glass cleaning (weekly), office mopping, sweeping & vacuuming (weekly), desk dusting (quarterly)' },
      { name: 'Restrooms (3)', tasks: 'Full sanitize & disinfect all fixtures, mop & disinfect floors, clean mirrors, empty & reline trash — weekly service' },
      { name: 'Break Room / Kitchen', tasks: 'Wipe countertops & tables, inside/outside microwave, outside of fridge & water machine, breakroom tables & chairs (weekly), inside fridge (monthly)' },
      { name: 'Warehouse / Production Floor', tasks: 'Dust mopping throughout (weekly)' },
      { name: 'Periodic Services', tasks: 'Baseboard cleaning (quarterly), QA inspections via OrangeQC reporting platform (weekly)' },
    ];

    // Two column layout
    const left = zones.slice(0, 3);
    const right = zones.slice(3);

    left.forEach((z, i) => {
      const y = 1.10 + i * 1.08;
      s.addText(z.name, { x: 0.5, y, w: 4.3, h: 0.26, fontSize: 12, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      s.addText(z.tasks, { x: 0.5, y: y + 0.28, w: 4.3, h: 0.62, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true });
      if (i < left.length - 1) hairline(s, 0.5, y + 0.96, 4.3);
    });

    vline(s, 5.0, 1.05, 3.8);

    right.forEach((z, i) => {
      const y = 1.10 + i * 1.08;
      s.addText(z.name, { x: 5.2, y, w: 4.3, h: 0.26, fontSize: 12, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      s.addText(z.tasks, { x: 5.2, y: y + 0.28, w: 4.3, h: 0.62, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true });
      if (i < right.length - 1) hairline(s, 5.2, y + 0.96, 4.3);
    });
  }

  // ── SLIDE 5: YOUR TEAM ───────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 5, 'YOUR TEAM');

    s.addText('Your Team. Not a Call Center.', {
      x: 0.5, y: 0.30, w: 9, h: 0.42, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Three people accountable to your facility — by name, by role, by phone.', {
      x: 0.5, y: 0.70, w: 9, h: 0.24, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.00, 9.0);

    const team = [
      {
        img: './hereford.png',
        name: 'Hereford Johnson',
        creds: 'US Air Force Veteran · SDVOSB · ISSA Member',
        title: 'CEO & Owner',
        stmt: 'Your primary contact. Reachable directly — no middlemen, no account managers.',
        x: 0.5
      },
      {
        img: './victoriana.png',
        name: 'Victoriana Johnson',
        creds: 'Operations Leadership · Client Relations',
        title: 'Director of Operations',
        stmt: 'Oversees scheduling, staffing, and service delivery across all accounts.',
        x: 3.65
      },
      {
        img: './johanna.png',
        name: 'Johanna Hernandez',
        creds: 'Certified QA Inspector · OrangeQC Certified',
        title: 'QA Manager',
        stmt: 'Conducts weekly inspections, files reports, and owns resolution follow-through.',
        x: 6.82
      }
    ];

    team.forEach((t, i) => {
      if (i > 0) vline(s, t.x - 0.17, 1.06, 3.55);
      // Circular headshot using image directly
      s.addImage({ path: t.img, x: t.x + 0.72, y: 1.12, w: 1.05, h: 1.05, rounding: true });
      s.addText(t.name, { x: t.x, y: 2.26, w: 2.8, h: 0.30, fontSize: 13, bold: true, color: NAVY, fontFace: 'Trebuchet MS', align: 'center' });
      s.addText(t.creds, { x: t.x, y: 2.56, w: 2.8, h: 0.30, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri', align: 'center', wrap: true });
      s.addText(t.title, { x: t.x, y: 2.88, w: 2.8, h: 0.24, fontSize: 10, bold: true, color: PROSPECT, fontFace: 'Calibri', align: 'center' });
      hairline(s, t.x, 3.16, 2.8);
      s.addText(t.stmt, { x: t.x, y: 3.22, w: 2.8, h: 0.65, fontSize: 10, color: MGRAY, fontFace: 'Calibri', align: 'center', wrap: true });
    });

    hairline(s, 0.5, 4.55, 9.0);
    s.addText('"I\'ve held the mop. I\'ve been the crew. That\'s why we\'re built around accountability, not excuses." — Hereford Johnson', {
      x: 0.5, y: 4.62, w: 8.5, h: 0.28, fontSize: 10, italic: true, color: MGRAY, fontFace: 'Calibri'
    });
  }

  // ── SLIDE 6: RAMP-UP PLAN ────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 6, 'RAMP-UP PLAN');

    s.addText('Your Ramp-Up. Before Day One.', {
      x: 0.5, y: 0.30, w: 9, h: 0.42, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hairline(s, 0.5, 0.78, 9.0);

    // Gantt setup
    const gx = 0.5;
    const gy = 0.86;
    const colW = 1.38;
    const rowH = 0.44;
    const labelW = 3.0;
    const cols = ['ACTIVITY', 'Wk -2', 'Wk -1', 'Week 1', 'Week 2', 'Mo. 2', 'Mo. 3'];
    const numCols = cols.length - 1; // data cols

    // Header row
    s.addShape('rect', { x: gx, y: gy, w: labelW, h: rowH, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText('ACTIVITY', { x: gx + 0.1, y: gy + 0.12, w: labelW - 0.1, h: 0.22, fontSize: 8, bold: true, color: GOLD, fontFace: 'Calibri', charSpacing: 2 });

    for (let c = 1; c < cols.length; c++) {
      const cx = gx + labelW + (c - 1) * colW;
      s.addShape('rect', { x: cx, y: gy, w: colW, h: rowH, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(cols[c], { x: cx, y: gy + 0.12, w: colW, h: 0.22, fontSize: 8, color: LGRAY, fontFace: 'Calibri', align: 'center' });
    }

    const activities = [
      { name: 'CEO + QA Manager Site Walk',      bars: [0,1], color: GOLD },
      { name: 'Key Handoff & Supply Staging',     bars: [0,1], color: GOLD },
      { name: 'Team Assignment & Orientation',    bars: [1],   color: GOLD },
      { name: 'Service Launch',                   bars: [2],   color: NAVY },
      { name: 'Daily Supervisor Check-Ins',       bars: [2,3], color: NAVY },
      { name: 'OrangeQC Baseline Report',         bars: [2,3], color: NAVY },
      { name: '30-Day Review Call',               bars: [4],   color: GREEN },
      { name: '90-Day QBR & Scope Review',        bars: [5],   color: GREEN },
    ];

    activities.forEach((act, i) => {
      const ry = gy + rowH + i * rowH;
      const rowColor = i % 2 === 0 ? WHITE : 'F4F7FB';
      // Row background (label area)
      s.addShape('rect', { x: gx, y: ry, w: labelW, h: rowH, fill: { color: rowColor }, line: { color: RULE } });
      s.addText(act.name, { x: gx + 0.1, y: ry + 0.12, w: labelW - 0.15, h: 0.22, fontSize: 9, color: DKGRAY, fontFace: 'Calibri' });

      // Data cells
      for (let c = 0; c < numCols; c++) {
        const cx = gx + labelW + c * colW;
        s.addShape('rect', { x: cx, y: ry, w: colW, h: rowH, fill: { color: rowColor }, line: { color: RULE } });
      }

      // Bars
      if (act.bars.length > 0) {
        const barStart = gx + labelW + act.bars[0] * colW + 0.06;
        const barEnd   = gx + labelW + (act.bars[act.bars.length - 1] + 1) * colW - 0.06;
        const barW = barEnd - barStart;
        s.addShape('rect', {
          x: barStart, y: ry + 0.10, w: barW, h: rowH * 0.55,
          fill: { color: act.color }, line: { color: act.color }
        });
      }
    });

    // Legend
    const legendY = gy + rowH + activities.length * rowH + 0.10;
    [[GOLD,'Pre-Start'], [NAVY,'Active Service'], [GREEN,'Milestone Review']].forEach(([c, label], i) => {
      const lx = 0.5 + i * 2.9;
      s.addShape('rect', { x: lx, y: legendY, w: 0.22, h: 0.14, fill: { color: c }, line: { color: c } });
      s.addText(label, { x: lx + 0.28, y: legendY - 0.01, w: 2.2, h: 0.16, fontSize: 8.5, color: MGRAY, fontFace: 'Calibri' });
    });
  }

  // ── SLIDE 7: SOCIAL PROOF ────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 7, 'CLIENT TESTIMONIALS');

    s.addText('What Our Clients Say.', {
      x: 0.5, y: 0.30, w: 7, h: 0.42, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Facilities that can\'t afford to get it wrong — and don\'t.', {
      x: 0.5, y: 0.70, w: 7, h: 0.24, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.00, 9.0);

    // Hero quote (manufacturing-relevant for LSI)
    s.addText(
      '"What impressed us most was their understanding of our compliance requirements. They didn\'t just clean — they followed our protocols, documented everything, and worked around our production schedule without missing a beat."',
      { x: 0.5, y: 1.10, w: 6.6, h: 0.90, fontSize: 13, italic: true, color: NAVY, fontFace: 'Georgia', wrap: true }
    );
    s.addText('— Manufacturing Plant Operations Manager', {
      x: 0.5, y: 2.02, w: 6.6, h: 0.22, fontSize: 9, color: LGRAY, fontFace: 'Calibri'
    });

    hairline(s, 0.5, 2.28, 6.6);

    // Two secondary quotes
    s.addText('"The team at MDF understands that in our environment, cleaning is part of our safety program — not just an afterthought."', {
      x: 0.5, y: 2.36, w: 3.1, h: 0.70, fontSize: 10, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Sheriff\'s Office Facility Manager', {
      x: 0.5, y: 3.08, w: 3.1, h: 0.20, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri'
    });

    s.addText('"We\'ve worked with several cleaning companies over the years, but Mad Dog is different. When there\'s an issue, they fix it immediately."', {
      x: 3.8, y: 2.36, w: 3.1, h: 0.70, fontSize: 10, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Government Administrator', {
      x: 3.8, y: 3.08, w: 3.1, h: 0.20, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri'
    });

    // Right stat panel
    vline(s, 7.30, 1.02, 3.60);

    const stats = [
      { stat: 'FAA', label: 'Certified Work History' },
      { stat: 'Army', label: 'Past Performance' },
      { stat: 'ISSA', label: 'Industry Member' }
    ];
    stats.forEach((st, i) => {
      const sy = 1.18 + i * 1.12;
      s.addText(st.stat, { x: 7.55, y: sy, w: 2.1, h: 0.52, fontSize: 22, bold: true, color: NAVY, fontFace: 'Trebuchet MS', align: 'center' });
      s.addText(st.label, { x: 7.55, y: sy + 0.54, w: 2.1, h: 0.22, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri', align: 'center' });
      if (i < stats.length - 1) hairline(s, 7.55, sy + 0.82, 2.1);
    });
  }

  // ── SLIDE 8: INVESTMENT + NEXT STEPS ────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 8, 'INVESTMENT & NEXT STEPS');

    // Left half
    s.addText('YOUR INVESTMENT', {
      x: 0.5, y: 0.30, w: 4.2, h: 0.20, fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('$1,000', {
      x: 0.5, y: 0.52, w: 4.2, h: 0.90, fontSize: 52, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('per month  ·  $12,000 annually  ·  Month-to-Month  ·  30-Day Notice', {
      x: 0.5, y: 1.42, w: 4.2, h: 0.22, fontSize: 9.5, color: MGRAY, fontFace: 'Calibri'
    });

    hairline(s, 0.5, 1.70, 4.2);

    // Line items
    const items = [
      { label: 'Labor — W-2 Employees', value: '$630', color: null },
      { label: 'Supplies & Consumables (4%)', value: '$40', color: null },
      { label: 'Equipment & Maintenance (3%)', value: '$30', color: null },
      { label: 'OrangeQC Reporting', value: 'Included', color: GREEN },
      { label: 'Dedicated QA Manager', value: 'Included', color: GREEN },
      { label: 'Ownership Direct Line', value: 'Included', color: GREEN },
    ];

    items.forEach((item, i) => {
      const iy = 1.80 + i * 0.34;
      const rowBg = i % 2 === 0 ? WHITE : 'F4F7FB';
      s.addShape('rect', { x: 0.48, y: iy, w: 4.22, h: 0.30, fill: { color: rowBg }, line: { color: rowBg } });
      s.addText(item.label, { x: 0.55, y: iy + 0.05, w: 2.8, h: 0.22, fontSize: 9.5, color: MGRAY, fontFace: 'Calibri' });
      s.addText(item.value, { x: 3.4, y: iy + 0.05, w: 1.2, h: 0.22, fontSize: 9.5, bold: true, color: item.color || DKGRAY, fontFace: 'Calibri', align: 'right' });
    });

    // Total bar
    const totalY = 1.80 + items.length * 0.34 + 0.06;
    s.addShape('rect', { x: 0.48, y: totalY, w: 4.22, h: 0.38, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText('Monthly Total', { x: 0.58, y: totalY + 0.08, w: 2.2, h: 0.24, fontSize: 10, color: WHITE, fontFace: 'Trebuchet MS', bold: true });
    s.addText('$1,000', { x: 2.8, y: totalY + 0.08, w: 1.8, h: 0.24, fontSize: 10, bold: true, color: GOLD, fontFace: 'Trebuchet MS', align: 'right' });

    // Vertical divider
    vline(s, 5.0, 0.26, 5.0);

    // Right half
    s.addText('READY TO MOVE FORWARD?', {
      x: 5.2, y: 0.30, w: 4.4, h: 0.20, fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('What happens when you say yes:', {
      x: 5.2, y: 0.52, w: 4.4, h: 0.48, fontSize: 20, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });

    const steps = [
      'Agreement signed & start date confirmed',
      'CEO + QA Manager schedule site walkthrough',
      'Team assigned, keys exchanged, supplies staged',
      'OrangeQC account created — you get login access',
      'First service delivered on your start date',
    ];

    steps.forEach((step, i) => {
      const sy = 1.10 + i * 0.52;
      s.addText(String(i + 1), { x: 5.2, y: sy, w: 0.30, h: 0.30, fontSize: 14, bold: true, color: GOLD, fontFace: 'Trebuchet MS' });
      hairline(s, 5.2, sy + 0.32, 0.30, GOLD);
      s.addText(step, { x: 5.60, y: sy + 0.04, w: 3.9, h: 0.30, fontSize: 10, color: MGRAY, fontFace: 'Calibri', wrap: true });
    });

    hairline(s, 5.2, 3.80, 4.4);

    s.addText('Hereford Johnson', { x: 5.2, y: 3.90, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: NAVY, fontFace: 'Trebuchet MS' });
    s.addText('623-321-2542  ·  office@maddogcleaning.com', {
      x: 5.2, y: 4.18, w: 4.4, h: 0.22, fontSize: 9.5, color: MGRAY, fontFace: 'Calibri'
    });
  }

  // ── SAVE ─────────────────────────────────────────────────────────────────────
  await prs.writeFile({ fileName: 'MDF_Proposal_LogicalSystems_2026-05-28.pptx' });
  console.log('Presentation saved: MDF_Proposal_LogicalSystems_2026-05-28.pptx');
}

buildProposal().catch(err => { console.error(err); process.exit(1); });
