const PptxGenJS = require('pptxgenjs');
const fs = require('fs');

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const NAVY   = '0D1F3C';
const WHITE  = 'FFFFFF';
const MGRAY  = '6B7280';
const LGRAY  = '9CA3AF';
const RULE   = 'D1D5DB';
const GOLD   = 'C9A84C';
const PROSPECT = '1B3A6B';
const GREEN  = '2E7D52';
const DKGRAY = '374151';
const ORANGE = 'F97316';  // OrangeQC brand accent

const SLIDE_W = 10;
const SLIDE_H = 5.625;

// ─── HELPERS ──────────────────────────────────────────────────────────────────
function addContentChrome(slide, prs, pageNum, overline) {
  slide.addShape(prs.ShapeType.rect, { x: 0, y: 0, w: SLIDE_W, h: 0.04, fill: { color: NAVY }, line: { color: NAVY } });
  if (overline) {
    slide.addText(overline, { x: 0.5, y: 0.10, w: 8, h: 0.18, fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5 });
  }
  slide.addText(String(pageNum), { x: 9.5, y: 0.08, w: 0.4, h: 0.18, fontSize: 8, color: LGRAY, fontFace: 'Calibri', align: 'right' });
  slide.addImage({ path: './mdf_logo_white_bg.png', x: 8.72, y: 5.10, w: 1.15, h: 0.44 });
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
    s.addImage({ path: './cover_photo.jpg', x: 0, y: 0, w: SLIDE_W, h: SLIDE_H });

    // All-white MDF logo top-left (white text, transparent bg, reads on dark photo)
    s.addImage({ path: './mdf_logo_all_white.png', x: 0.38, y: 0.30, w: 1.10, h: 0.65 });

    s.addText('PREPARED FOR', {
      x: 0.5, y: 3.55, w: 6, h: 0.20,
      fontSize: 7, bold: true, color: 'A8B8CC', fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('Logical Systems Inc.', {
      x: 0.5, y: 3.76, w: 8, h: 0.82,
      fontSize: 34, bold: true, color: WHITE, fontFace: 'Trebuchet MS'
    });
    s.addShape('rect', { x: 0.5, y: 4.58, w: 7.0, h: 0.018, fill: { color: '5A6A7A' }, line: { color: '5A6A7A' } });
    s.addText('Facility Services Proposal  ·  April Bocox, Health and Safety Coordinator  ·  May 28, 2026', {
      x: 0.5, y: 4.62, w: 9, h: 0.22,
      fontSize: 9, color: '8B9BAD', fontFace: 'Calibri'
    });
  }

  // ── SLIDE 2: WHY MDF ────────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 2, 'WHY MAD DOG FACILITY PARTNERS');

    s.addText('You can choose any janitorial company.', {
      x: 0.5, y: 0.28, w: 9, h: 0.48, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Here is why our clients stay for an average of 6 years.', {
      x: 0.5, y: 0.76, w: 9, h: 0.26, fontSize: 12, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.08, 9.0);

    const cols = [
      {
        x: 0.5, stat: '92%+', label: 'avg. inspection score', title: 'Real-Time Quality Assurance',
        body: 'Every service is tracked through a third-party inspection platform. Scores are logged, time-stamped, and available to you in real time. You never have to wonder if the work was done.'
      },
      {
        x: 3.65, stat: '<24hr', label: 'avg. resolution time', title: 'Documented Service Resolution',
        body: 'Every issue generates a service ticket with a timestamp and assigned owner. Problems are tracked from open to closed — nothing falls through the cracks and no response goes undocumented.'
      },
      {
        x: 6.82, stat: 'CEO', label: 'is your primary contact', title: 'Direct Executive Access',
        body: 'Hereford Johnson, US Air Force veteran and company founder, picks up the phone. No account managers, no call routing, no corporate layers between you and the person responsible.'
      }
    ];

    cols.forEach((c, i) => {
      if (i > 0) vline(s, c.x - 0.17, 1.12, 4.10);
      s.addText(c.stat, { x: c.x, y: 1.18, w: 2.9, h: 0.90, fontSize: 48, bold: true, color: NAVY, fontFace: 'Trebuchet MS' });
      s.addText(c.label, { x: c.x, y: 2.10, w: 2.9, h: 0.24, fontSize: 10, color: LGRAY, fontFace: 'Calibri' });
      hairline(s, c.x, 2.38, 2.9);
      s.addText(c.title, { x: c.x, y: 2.46, w: 2.9, h: 0.30, fontSize: 13, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      s.addText(c.body, { x: c.x, y: 2.82, w: 2.9, h: 1.30, fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true });
    });

    hairline(s, 0.5, 4.50, 9.0);
    s.addText('"We surveyed our clients on what we should do more of. The #1 answer was communication and integrity. We believe this is why our average client has been with us for 6 years."', {
      x: 0.5, y: 4.56, w: 8.8, h: 0.40, fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
  }

  // ── SLIDE 3: WE UNDERSTAND YOUR FACILITY ────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 3, 'YOUR FACILITY');

    s.addText('We built this for Logical Systems.', {
      x: 0.5, y: 0.28, w: 5.4, h: 0.52, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hairline(s, 0.5, 0.86, 5.4);

    s.addText(
      'LSI operates manufacturing and industrial facilities where precision, compliance, and uptime are non-negotiable. ' +
      'Your environment demands cleaning that works around production schedules, protects sensitive controls equipment, and meets the documentation standards your own clients expect from you.\n\n' +
      'MDF delivers compliance-ready facility services designed for automation and controls environments. We coordinate around your production calendar, document every service, and treat your facility with the same operational discipline your team applies to every project.',
      { x: 0.5, y: 0.96, w: 5.4, h: 2.10, fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true }
    );

    s.addText('Your core values — service, integrity, and excellence — are the same values we build our teams around. That alignment isn\'t coincidental. It\'s why this works.', {
      x: 0.5, y: 3.18, w: 5.4, h: 0.60, fontSize: 11, italic: true, color: PROSPECT, fontFace: 'Calibri', wrap: true
    });

    vline(s, 6.05, 0.26, 4.65);

    const facts = [
      { stat: 'Manufacturing / Automation', label: 'INDUSTRY' },
      { stat: 'Controls Integrator Since 1985', label: 'FACILITY PROFILE' },
      { stat: 'OSHA / Production-Grade', label: 'COMPLIANCE CONTEXT' },
    ];

    facts.forEach((f, i) => {
      const y = 0.55 + i * 1.40;
      s.addText(f.label, { x: 6.28, y, w: 3.4, h: 0.20, fontSize: 7.5, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 2.5 });
      s.addText(f.stat, { x: 6.28, y: y + 0.24, w: 3.4, h: 0.50, fontSize: 16, bold: true, color: NAVY, fontFace: 'Trebuchet MS', wrap: true });
      if (i < facts.length - 1) hairline(s, 6.28, y + 0.84, 3.4);
    });
  }

  // ── SLIDE 4: SCOPE OF WORK ───────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 4, 'SCOPE OF WORK');

    s.addText('Your Facility. Your Scope.', {
      x: 0.5, y: 0.28, w: 9, h: 0.48, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Weekly service  ·  Start July 1, 2026  ·  Month-to-Month  ·  30-Day Notice', {
      x: 0.5, y: 0.76, w: 9, h: 0.26, fontSize: 11, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.08, 9.0);

    const zones = [
      { name: 'Offices & Common Areas', tasks: 'General dusting, front glass cleaning, office mopping/sweeping/vacuuming (weekly); desk dusting (quarterly)' },
      { name: 'Restrooms — 3 Total', tasks: 'Full sanitize & disinfect all fixtures, mop & disinfect floors, clean mirrors & chrome, empty & reline trash (weekly)' },
      { name: 'Break Room / Kitchen', tasks: 'Wipe countertops & tables, inside & outside of microwave, outside of fridge & water machine, breakroom tables & chairs (weekly); inside fridge (monthly)' },
      { name: 'Warehouse / Production Floor', tasks: 'Full dust mopping throughout (weekly)' },
      { name: 'Periodic Services', tasks: 'Baseboard cleaning (quarterly); OrangeQC quality inspection reports (weekly)' },
    ];

    const left = zones.slice(0, 3);
    const right = zones.slice(3);

    const rowH = 1.24;
    left.forEach((z, i) => {
      const y = 1.16 + i * rowH;
      s.addText(z.name, { x: 0.5, y, w: 4.3, h: 0.28, fontSize: 12, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      s.addText(z.tasks, { x: 0.5, y: y + 0.32, w: 4.3, h: 0.82, fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true });
      if (i < left.length - 1) hairline(s, 0.5, y + rowH - 0.06, 4.3);
    });

    vline(s, 5.05, 1.12, 3.85);

    right.forEach((z, i) => {
      const y = 1.16 + i * rowH;
      s.addText(z.name, { x: 5.25, y, w: 4.3, h: 0.28, fontSize: 12, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      s.addText(z.tasks, { x: 5.25, y: y + 0.32, w: 4.3, h: 0.82, fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true });
      if (i < right.length - 1) hairline(s, 5.25, y + rowH - 0.06, 4.3);
    });
  }

  // ── SLIDE 5: YOUR TEAM ───────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 5, 'YOUR TEAM');

    s.addText('Your Team. Not a Call Center.', {
      x: 0.5, y: 0.28, w: 9, h: 0.48, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Three people accountable to your facility — by name, by role, by phone.', {
      x: 0.5, y: 0.76, w: 9, h: 0.26, fontSize: 12, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.08, 9.0);

    const team = [
      {
        img: './hereford.png',
        name: 'Hereford Johnson',
        creds: 'US Air Force Veteran · SDVOSB · ISSA Member',
        title: 'CEO & Owner',
        stmt: 'Your primary contact. Picks up the phone personally — no account managers, no call routing, no corporate layers between you and the person accountable.',
        x: 0.5
      },
      {
        img: './victoriana.png',
        name: 'Victoriana Johnson',
        creds: 'Certified QA Inspector · OrangeQC Platform',
        title: 'QA Manager',
        stmt: 'Conducts weekly on-site inspections, logs every score in OrangeQC, and personally owns resolution follow-through on every open ticket.',
        x: 3.65
      },
      {
        img: './johanna.png',
        name: 'Johanna Hernandez',
        creds: 'Talent Acquisition · Training & Certification',
        title: 'Area Talent Manager',
        stmt: 'Handles recruiting, vetting, and ongoing training of custodial staff. Ensures every person assigned to your facility is background-checked, trained, and accountable.',
        x: 6.82
      }
    ];

    team.forEach((t, i) => {
      if (i > 0) vline(s, t.x - 0.17, 1.12, 4.08);
      s.addImage({ path: t.img, x: t.x + 0.75, y: 1.18, w: 1.05, h: 1.05, rounding: true });
      s.addText(t.name, { x: t.x, y: 2.30, w: 2.9, h: 0.30, fontSize: 13, bold: true, color: NAVY, fontFace: 'Trebuchet MS', align: 'center' });
      s.addText(t.creds, { x: t.x, y: 2.62, w: 2.9, h: 0.30, fontSize: 9, color: LGRAY, fontFace: 'Calibri', align: 'center', wrap: true });
      s.addText(t.title, { x: t.x, y: 2.94, w: 2.9, h: 0.24, fontSize: 11, bold: true, color: PROSPECT, fontFace: 'Calibri', align: 'center' });
      hairline(s, t.x, 3.22, 2.9);
      s.addText(t.stmt, { x: t.x, y: 3.30, w: 2.9, h: 1.08, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', align: 'left', wrap: true });
    });

    hairline(s, 0.5, 4.52, 9.0);
    s.addText('"I\'ve held the mop. I\'ve been the crew. That\'s why we\'re built around accountability, not excuses." — Hereford Johnson, CEO', {
      x: 0.5, y: 4.58, w: 8.8, h: 0.28, fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri'
    });
  }

  // ── SLIDE 6: QUALITY ASSURANCE — ORANGEQC ───────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 6, 'QUALITY ASSURANCE');

    // Left content panel (~54% width)
    s.addText('You Get Full Visibility Into Every Clean.', {
      x: 0.5, y: 0.28, w: 5.4, h: 0.52, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hairline(s, 0.5, 0.86, 5.4);

    s.addText(
      'Every MDF service is backed by a mobile inspection and ticketing platform that gives you real-time visibility into what\'s happening inside your facility.\n\n' +
      'This is not an internal tool — it\'s a client-facing layer of accountability. You receive access to your own dashboard where inspection scores, service tickets, and resolution timelines are logged automatically after every visit.',
      { x: 0.5, y: 0.96, w: 5.4, h: 1.72, fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true }
    );

    hairline(s, 0.5, 2.76, 5.4);

    // Three feature rows
    const features = [
      { label: 'Inspection Scoring', desc: 'Every area graded at each visit. Scores trend over time — you see if standards are holding.' },
      { label: 'Service Tickets', desc: 'Any flagged issue creates a ticket, assigned and time-stamped. Resolution tracked to close.' },
      { label: 'Documented History', desc: 'Full audit trail of every service. Useful for compliance reviews, audits, and accountability records.' },
    ];
    features.forEach((f, i) => {
      const fy = 2.86 + i * 0.72;
      s.addText(f.label, { x: 0.5, y: fy, w: 1.65, h: 0.24, fontSize: 11, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS' });
      s.addText(f.desc, { x: 2.22, y: fy, w: 3.6, h: 0.50, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true });
      if (i < features.length - 1) hairline(s, 0.5, fy + 0.62, 5.4);
    });

    // "Included at no extra charge" callout
    hairline(s, 0.5, 5.00, 5.4);
    s.addText('Included with every MDF contract — at no additional charge.', {
      x: 0.5, y: 5.06, w: 5.4, h: 0.22, fontSize: 10.5, italic: true, bold: false, color: GREEN, fontFace: 'Calibri'
    });

    // Right panel — stat column
    vline(s, 6.05, 0.26, 4.85);

    const qcStats = [
      { stat: '90%+', label: 'TARGET INSPECTION SCORE', sub: 'Tracked and reported every week' },
      { stat: '<2hr', label: 'AVERAGE RESPONSE TIME', sub: 'From ticket open to acknowledgment' },
      { stat: '<24hr', label: 'AVERAGE RESOLUTION TIME', sub: 'From issue flagged to issue closed' },
    ];
    qcStats.forEach((st, i) => {
      const sy = 0.48 + i * 1.52;
      s.addText(st.label, { x: 6.28, y: sy, w: 3.4, h: 0.20, fontSize: 7.5, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 2.5 });
      s.addText(st.stat, { x: 6.28, y: sy + 0.22, w: 3.4, h: 0.72, fontSize: 42, bold: true, color: NAVY, fontFace: 'Trebuchet MS' });
      s.addText(st.sub, { x: 6.28, y: sy + 0.96, w: 3.4, h: 0.30, fontSize: 9.5, color: MGRAY, fontFace: 'Calibri', wrap: true });
      if (i < qcStats.length - 1) hairline(s, 6.28, sy + 1.36, 3.4);
    });
  }

  // ── SLIDE 7: RAMP-UP PLAN ────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 7, 'RAMP-UP PLAN');

    s.addText('Your Ramp-Up. Before Day One.', {
      x: 0.5, y: 0.28, w: 9, h: 0.48, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hairline(s, 0.5, 0.82, 9.0);

    const gx = 0.5;
    const gy = 0.90;
    const colW = 1.38;
    const rowH = 0.48;
    const labelW = 3.05;
    const cols = ['ACTIVITY', 'Wk -2', 'Wk -1', 'Week 1', 'Week 2', 'Mo. 2', 'Mo. 3'];
    const numCols = cols.length - 1;

    // Header row
    s.addShape('rect', { x: gx, y: gy, w: labelW, h: rowH, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText('ACTIVITY', { x: gx + 0.10, y: gy + 0.14, w: labelW - 0.1, h: 0.22, fontSize: 8, bold: true, color: GOLD, fontFace: 'Calibri', charSpacing: 2 });
    for (let c = 1; c < cols.length; c++) {
      const cx = gx + labelW + (c - 1) * colW;
      s.addShape('rect', { x: cx, y: gy, w: colW, h: rowH, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(cols[c], { x: cx, y: gy + 0.14, w: colW, h: 0.22, fontSize: 9, color: LGRAY, fontFace: 'Calibri', align: 'center' });
    }

    const activities = [
      { name: 'CEO + QA Manager Site Walk',    bars: [0,1], color: GOLD },
      { name: 'Key Handoff & Supply Staging',  bars: [0,1], color: GOLD },
      { name: 'Team Assignment & Orientation', bars: [1],   color: GOLD },
      { name: 'Service Launch',                bars: [2],   color: NAVY },
      { name: 'Daily Supervisor Check-Ins',    bars: [2,3], color: NAVY },
      { name: 'OrangeQC Baseline Report',      bars: [2,3], color: NAVY },
      { name: '30-Day Review Call',            bars: [4],   color: GREEN },
      { name: '90-Day QBR & Scope Review',     bars: [5],   color: GREEN },
    ];

    activities.forEach((act, i) => {
      const ry = gy + rowH + i * rowH;
      const rowColor = i % 2 === 0 ? WHITE : 'F4F7FB';
      s.addShape('rect', { x: gx, y: ry, w: labelW, h: rowH, fill: { color: rowColor }, line: { color: RULE } });
      s.addText(act.name, { x: gx + 0.10, y: ry + 0.13, w: labelW - 0.15, h: 0.24, fontSize: 9.5, color: DKGRAY, fontFace: 'Calibri' });

      for (let c = 0; c < numCols; c++) {
        const cx = gx + labelW + c * colW;
        s.addShape('rect', { x: cx, y: ry, w: colW, h: rowH, fill: { color: rowColor }, line: { color: RULE } });
      }

      if (act.bars.length > 0) {
        const barStart = gx + labelW + act.bars[0] * colW + 0.07;
        const barEnd   = gx + labelW + (act.bars[act.bars.length - 1] + 1) * colW - 0.07;
        s.addShape('rect', {
          x: barStart, y: ry + 0.11, w: barEnd - barStart, h: rowH * 0.55,
          fill: { color: act.color }, line: { color: act.color }
        });
      }
    });

    const legendY = gy + rowH + activities.length * rowH + 0.12;
    [[GOLD,'Pre-Start'], [NAVY,'Active Service'], [GREEN,'Milestone Review']].forEach(([c, label], i) => {
      const lx = 0.5 + i * 3.0;
      s.addShape('rect', { x: lx, y: legendY, w: 0.24, h: 0.15, fill: { color: c }, line: { color: c } });
      s.addText(label, { x: lx + 0.32, y: legendY - 0.01, w: 2.4, h: 0.18, fontSize: 9, color: MGRAY, fontFace: 'Calibri' });
    });
  }

  // ── SLIDE 8: SOCIAL PROOF ────────────────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 8, 'CLIENT TESTIMONIALS');

    s.addText('What Our Clients Say.', {
      x: 0.5, y: 0.28, w: 7, h: 0.48, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Facilities that can\'t afford to get it wrong — and don\'t.', {
      x: 0.5, y: 0.76, w: 7, h: 0.26, fontSize: 12, color: MGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 1.08, 9.0);

    // Hero quote
    s.addText(
      '"What impressed us most was their understanding of our compliance requirements. They didn\'t just clean — they followed our protocols, documented everything, and worked around our production schedule without missing a beat."',
      { x: 0.5, y: 1.18, w: 6.6, h: 1.00, fontSize: 13, italic: true, color: NAVY, fontFace: 'Georgia', wrap: true }
    );
    s.addText('— Manufacturing Plant Operations Manager', {
      x: 0.5, y: 2.20, w: 6.6, h: 0.22, fontSize: 9.5, color: LGRAY, fontFace: 'Calibri'
    });
    hairline(s, 0.5, 2.48, 6.6);

    // Two secondary quotes
    s.addText('"The team at MDF understands that in our environment, cleaning is part of our safety program — not just an afterthought."', {
      x: 0.5, y: 2.58, w: 3.1, h: 0.80, fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Sheriff\'s Office Facility Manager', {
      x: 0.5, y: 3.40, w: 3.1, h: 0.20, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri'
    });

    s.addText('"We\'ve worked with several cleaning companies over the years, but Mad Dog is different. When there\'s an issue, they fix it immediately."', {
      x: 3.75, y: 2.58, w: 3.1, h: 0.80, fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Government Administrator', {
      x: 3.75, y: 3.40, w: 3.1, h: 0.20, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri'
    });

    vline(s, 7.32, 1.10, 3.80);

    const stats = [
      { stat: 'FAA', label: 'CERTIFIED PAST PERFORMANCE' },
      { stat: 'Army', label: 'PAST PERFORMANCE' },
      { stat: 'ISSA', label: 'INDUSTRY MEMBER' },
    ];
    stats.forEach((st, i) => {
      const sy = 1.28 + i * 1.24;
      s.addText(st.stat, { x: 7.56, y: sy, w: 2.1, h: 0.58, fontSize: 26, bold: true, color: NAVY, fontFace: 'Trebuchet MS', align: 'center' });
      s.addText(st.label, { x: 7.56, y: sy + 0.60, w: 2.1, h: 0.22, fontSize: 8, bold: true, color: LGRAY, fontFace: 'Calibri', align: 'center', charSpacing: 1.5 });
      if (i < stats.length - 1) hairline(s, 7.56, sy + 0.90, 2.1);
    });

    // Third quote bottom
    hairline(s, 0.5, 3.72, 6.6);
    s.addText('"The background checks and professionalism of their crew gave us confidence from day one. In a government facility, security and accountability aren\'t negotiable. Mad Dog gets that."', {
      x: 0.5, y: 3.80, w: 6.6, h: 0.56, fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Municipal Building Supervisor', {
      x: 0.5, y: 4.38, w: 6.6, h: 0.20, fontSize: 8.5, color: LGRAY, fontFace: 'Calibri'
    });
  }

  // ── SLIDE 9: INVESTMENT + NEXT STEPS ────────────────────────────────────────
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addContentChrome(s, prs, 9, 'YOUR INVESTMENT & NEXT STEPS');

    // Left half
    s.addText('YOUR INVESTMENT', {
      x: 0.5, y: 0.28, w: 4.3, h: 0.20, fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('$1,000', {
      x: 0.5, y: 0.48, w: 4.3, h: 0.96, fontSize: 56, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('per month  ·  $12,000 annually  ·  Month-to-Month  ·  30-Day Notice', {
      x: 0.5, y: 1.44, w: 4.3, h: 0.22, fontSize: 9.5, color: MGRAY, fontFace: 'Calibri'
    });

    hairline(s, 0.5, 1.72, 4.3);

    const items = [
      { label: 'Labor — W-2 Employees',        value: '$630',     color: null },
      { label: 'Supplies & Consumables (4%)',   value: '$40',      color: null },
      { label: 'Equipment & Maintenance (3%)',  value: '$30',      color: null },
      { label: 'QA Inspection Reports',         value: 'Included', color: GREEN },
      { label: 'Dedicated QA Manager',          value: 'Included', color: GREEN },
      { label: 'Ownership Direct Line',         value: 'Included', color: GREEN },
    ];

    items.forEach((item, i) => {
      const iy = 1.82 + i * 0.36;
      const rowBg = i % 2 === 0 ? WHITE : 'F4F7FB';
      s.addShape('rect', { x: 0.48, y: iy, w: 4.32, h: 0.32, fill: { color: rowBg }, line: { color: rowBg } });
      s.addText(item.label, { x: 0.58, y: iy + 0.06, w: 2.9, h: 0.22, fontSize: 10, color: MGRAY, fontFace: 'Calibri' });
      s.addText(item.value, { x: 3.5, y: iy + 0.06, w: 1.2, h: 0.22, fontSize: 10, bold: true, color: item.color || DKGRAY, fontFace: 'Calibri', align: 'right' });
    });

    const totalY = 1.82 + items.length * 0.36 + 0.08;
    s.addShape('rect', { x: 0.48, y: totalY, w: 4.32, h: 0.42, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText('Monthly Total', { x: 0.60, y: totalY + 0.10, w: 2.4, h: 0.24, fontSize: 11, color: WHITE, fontFace: 'Trebuchet MS', bold: true });
    s.addText('$1,000', { x: 2.8, y: totalY + 0.10, w: 1.9, h: 0.24, fontSize: 11, bold: true, color: GOLD, fontFace: 'Trebuchet MS', align: 'right' });

    vline(s, 5.02, 0.24, 5.15);

    // Right half
    s.addText('READY TO MOVE FORWARD?', {
      x: 5.22, y: 0.28, w: 4.5, h: 0.20, fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('What happens when you say yes:', {
      x: 5.22, y: 0.50, w: 4.5, h: 0.52, fontSize: 20, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });

    const steps = [
      'Agreement signed & start date confirmed',
      'CEO + QA Manager schedule site walkthrough',
      'Team assigned, keys exchanged, supplies staged',
      'QA inspection account created — you get dashboard access',
      'First service delivered on your start date, July 1',
    ];
    steps.forEach((step, i) => {
      const sy = 1.14 + i * 0.56;
      s.addText(String(i + 1), { x: 5.22, y: sy, w: 0.32, h: 0.32, fontSize: 15, bold: true, color: GOLD, fontFace: 'Trebuchet MS' });
      hairline(s, 5.22, sy + 0.36, 0.32, GOLD);
      s.addText(step, { x: 5.64, y: sy + 0.05, w: 4.0, h: 0.36, fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true });
    });

    hairline(s, 5.22, 4.00, 4.5);
    s.addText('Hereford Johnson', { x: 5.22, y: 4.10, w: 4.5, h: 0.30, fontSize: 13, bold: true, color: NAVY, fontFace: 'Trebuchet MS' });
    s.addText('623-321-2542  ·  office@maddogcleaning.com', {
      x: 5.22, y: 4.40, w: 4.5, h: 0.24, fontSize: 10, color: MGRAY, fontFace: 'Calibri'
    });
  }

  await prs.writeFile({ fileName: 'MDF_Proposal_LogicalSystems_2026-05-28.pptx' });
  console.log('Presentation saved: MDF_Proposal_LogicalSystems_2026-05-28.pptx');
}

buildProposal().catch(err => { console.error(err); process.exit(1); });
