const PptxGenJS = require('pptxgenjs');
const fs = require('fs');

// ─── COLOR CONSTANTS (no # prefix — pptxgenjs bug) ────────────────────────────
const NAVY    = '0D1F3C';
const WHITE   = 'FFFFFF';
const MGRAY   = '6B7280';
const LGRAY   = '9CA3AF';
const RULE    = 'D1D5DB';
const GOLD    = 'C9A84C';
const PROSPECT = '1B3A6B';
const GREEN   = '2E7D52';
const DKGRAY  = '374151';
const BAND_W  = 'F4F7FB';
const BAND_M  = 'F8F9FA';

// ─── LAYOUT CONSTANTS ────────────────────────────────────────────────────────
const SW     = 10.0;    // slide width
const SH     = 5.625;   // slide height
const LM     = 0.5;     // left margin
const RM     = 9.6;     // right content edge
const CW     = RM - LM; // 9.1" usable width
const CT_TOP = 1.08;    // content top (below header/overline/headline)
const CT_BOT = 5.08;    // content bottom (above footer logo)
const CT_H   = CT_BOT - CT_TOP; // 4.0" usable content height

// ─── LAYOUT VALIDATOR ────────────────────────────────────────────────────────
function validateSlide(slideName, elements) {
  let maxBottom = 0;
  elements.forEach(el => {
    const bottom = el.y + el.h;
    if (bottom > SH) console.error(`  OVERFLOW [${slideName}] "${el.name}" extends to ${bottom.toFixed(2)}"`);
    if (bottom > maxBottom) maxBottom = bottom;
  });
  const dead = CT_BOT - maxBottom;
  if (dead > 0.35) console.warn(`  DEAD SPACE [${slideName}] ${dead.toFixed(2)}" unused — expand content`);
  return maxBottom;
}

// ─── CHROME (every content slide) ────────────────────────────────────────────
function addChrome(s, prs, pageNum, overline) {
  // Top navy rule
  s.addShape(prs.ShapeType.rect, { x: 0, y: 0, w: SW, h: 0.04, fill: { color: NAVY }, line: { color: NAVY } });
  // Overline
  if (overline) {
    s.addText(overline, {
      x: LM, y: 0.10, w: 7.5, h: 0.18,
      fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
  }
  // Page number top-right
  s.addText(String(pageNum), {
    x: 9.4, y: 0.08, w: 0.5, h: 0.18,
    fontSize: 8, color: LGRAY, fontFace: 'Calibri', align: 'right'
  });
  // MDF logo bottom-right
  s.addImage({ path: './mdf_logo_white_bg.png', x: 8.68, y: 5.06, w: 1.18, h: 0.45 });
}

// ─── SHAPE HELPERS ───────────────────────────────────────────────────────────
function hl(s, x, y, w, color) {
  s.addShape('rect', { x, y, w, h: 0.018, fill: { color: color || RULE }, line: { color: color || RULE } });
}
function vl(s, x, y, h, color) {
  s.addShape('rect', { x, y, w: 0.018, h, fill: { color: color || RULE }, line: { color: color || RULE } });
}

// ─── BUILD ────────────────────────────────────────────────────────────────────
async function build() {
  const prs = new PptxGenJS();
  prs.layout = 'LAYOUT_WIDE';

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 1 — COVER
  // Layout: full-bleed background via s.background, text anchored bottom-left
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    // CORRECTION 6: must use s.background, never addImage for cover
    s.background = { path: './cover_photo.jpg' };

    // MDF logo top-left — all-white version reads against dark photo
    s.addImage({ path: './mdf_logo_all_white.png', x: 0.38, y: 0.28, w: 1.15, h: 0.68 });

    // Bottom-left text block
    s.addText('PREPARED FOR', {
      x: LM, y: 3.45, w: 7, h: 0.20,
      fontSize: 7, bold: true, color: 'A8B8CC', fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('Logical Systems Inc.', {
      x: LM, y: 3.66, w: 8.5, h: 0.90,
      fontSize: 36, bold: true, color: WHITE, fontFace: 'Trebuchet MS'
    });
    s.addShape('rect', {
      x: LM, y: 4.58, w: 7.2, h: 0.018,
      fill: { color: '5A6A7A' }, line: { color: '5A6A7A' }
    });
    s.addText('Facility Services Proposal  ·  April Bocox, Health and Safety Coordinator  ·  May 28, 2026', {
      x: LM, y: 4.64, w: 9.2, h: 0.24,
      fontSize: 9.5, color: '8B9BAD', fontFace: 'Calibri'
    });
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 2 — WHY MDF
  // Layout: three equal columns with vertical hairline rules, stats as hero
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 2, 'WHY MAD DOG FACILITY PARTNERS');

    s.addText('You can choose any janitorial company.', {
      x: LM, y: 0.28, w: CW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Here is why our clients stay for an average of 6 years.', {
      x: LM, y: 0.78, w: CW, h: 0.26, fontSize: 12, color: MGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 1.08, CW);

    // 3 columns: each 2.9" wide, separated by vertical hairlines at x=3.57 and x=6.63
    const COL_W = 2.88;
    const cols = [
      {
        x: LM,
        stat: '92%+', label: 'avg. inspection score', title: 'Real-Time Quality Assurance',
        body: 'Every service is tracked through a third-party inspection platform. Scores are logged, time-stamped, and available to you in real time. You never have to wonder if the work was done — or how well.'
      },
      {
        x: 3.56,
        stat: '<24hr', label: 'avg. resolution time', title: 'Documented Service Resolution',
        body: 'Every issue generates a service ticket with a timestamp and assigned owner. Problems are tracked from open to closed — nothing falls through the cracks and every response is documented.'
      },
      {
        x: 6.62,
        stat: 'CEO', label: 'is your primary contact', title: 'Direct Executive Access',
        body: 'Hereford Johnson, US Air Force veteran and company founder, picks up the phone. No account managers, no call routing, no corporate layers between you and the person ultimately responsible.'
      }
    ];

    cols.forEach((c, i) => {
      if (i > 0) vl(s, c.x - 0.14, 1.10, 3.96);
      s.addText(c.stat, {
        x: c.x, y: 1.16, w: COL_W, h: 0.95,
        fontSize: 50, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
      });
      s.addText(c.label, {
        x: c.x, y: 2.12, w: COL_W, h: 0.26,
        fontSize: 10, color: LGRAY, fontFace: 'Calibri'
      });
      hl(s, c.x, 2.42, COL_W);
      s.addText(c.title, {
        x: c.x, y: 2.50, w: COL_W, h: 0.30,
        fontSize: 13, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS'
      });
      s.addText(c.body, {
        x: c.x, y: 2.84, w: COL_W, h: 1.62,
        fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true
      });
    });

    hl(s, LM, 4.54, CW);
    s.addText('"We surveyed our clients on what we should do more of. The #1 answer was communication and integrity. We believe this is why our average client has been with us for 6 years."', {
      x: LM, y: 4.60, w: CW, h: 0.44,
      fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });

    validateSlide('Why MDF', [
      { name: 'headline', y: 0.28, h: 0.50 },
      { name: 'columns', y: 1.16, h: 3.30 },
      { name: 'pullquote', y: 4.60, h: 0.44 }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 3 — YOUR FACILITY
  // Layout: left 58% narrative prose + pull-quote, right 38% stacked stat rows
  //         separated by horizontal rules only — NO vertical hairline rule
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 3, 'YOUR FACILITY');

    const LW = 5.40;  // left zone width
    const RX = 6.00;  // right zone x start
    const RW = 3.56;  // right zone width

    s.addText('We built this for Logical Systems.', {
      x: LM, y: 0.28, w: LW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hl(s, LM, 0.84, LW);

    s.addText(
      'LSI operates manufacturing and industrial facilities where precision, compliance, and uptime are non-negotiable. ' +
      'Your environment demands cleaning that works around production schedules, protects sensitive controls equipment, ' +
      'and meets the documentation standards your own clients expect from you.\n\n' +
      'MDF delivers compliance-ready facility services designed for automation and controls environments. ' +
      'We coordinate around your production calendar, document every service, and treat your facility with ' +
      'the same operational discipline your team applies to every project.\n\n' +
      'LSI\'s first customer from 1985 is still active today. Our oldest client relationship is 12 years. ' +
      'Retention isn\'t accidental — it\'s the product of showing up consistently and fixing problems fast.',
      {
        x: LM, y: 0.94, w: LW, h: 2.62,
        fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true
      }
    );

    hl(s, LM, 3.64, LW);
    s.addText(
      '"Your core values — service, integrity, and excellence — are the same values we build our teams around. ' +
      'That alignment isn\'t coincidental. It\'s why this partnership works."',
      {
        x: LM, y: 3.72, w: LW, h: 0.72,
        fontSize: 11, italic: true, color: PROSPECT, fontFace: 'Calibri', wrap: true
      }
    );
    hl(s, LM, 4.52, LW);
    s.addText('— Hereford Johnson, CEO, Mad Dog Facility Partners', {
      x: LM, y: 4.58, w: LW, h: 0.24,
      fontSize: 9, color: LGRAY, fontFace: 'Calibri'
    });

    // Right zone — three stat rows separated by horizontal rules (no vline)
    const facts = [
      { stat: 'Manufacturing / Automation', label: 'INDUSTRY TYPE' },
      { stat: 'Controls Integrator Since 1985', label: 'FACILITY PROFILE' },
      { stat: 'OSHA / Production-Grade', label: 'COMPLIANCE CONTEXT' },
    ];
    const STAT_ROW_H = 1.40;
    facts.forEach((f, i) => {
      const y = 0.50 + i * STAT_ROW_H;
      s.addText(f.label, {
        x: RX, y, w: RW, h: 0.22,
        fontSize: 7.5, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 2.5
      });
      s.addText(f.stat, {
        x: RX, y: y + 0.26, w: RW, h: 0.56,
        fontSize: 18, bold: true, color: NAVY, fontFace: 'Trebuchet MS', wrap: true
      });
      if (i < facts.length - 1) hl(s, RX, y + 1.00, RW);
    });

    validateSlide('Facility', [
      { name: 'prose', y: 0.94, h: 2.62 },
      { name: 'pull-quote', y: 3.72, h: 0.72 },
      { name: 'attribution', y: 4.58, h: 0.24 },
      { name: 'stats', y: 0.50, h: 3 * STAT_ROW_H }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 4 — SCOPE OF WORK
  // Layout: three horizontal frequency bands stacked full-width
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 4, 'SCOPE OF WORK');

    s.addText('Your Facility. Your Scope.', {
      x: LM, y: 0.28, w: CW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Weekly service  ·  Start July 1, 2026  ·  Month-to-Month  ·  30-Day Notice', {
      x: LM, y: 0.78, w: CW, h: 0.26, fontSize: 11, color: MGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 1.08, CW);

    // Weekly tasks (9) in 2 columns of 4–5 rows each
    const weeklyLeft = [
      'Restrooms (3): sanitize & disinfect all fixtures',
      'Restrooms: mop & disinfect floors, clean mirrors',
      'General dusting — all areas',
      'Front glass cleaning',
      'Office mopping, sweeping & vacuuming',
    ];
    const weeklyRight = [
      'Break room countertops, tables & chairs',
      'Microwave — inside & outside',
      'Refrigerator & water machine exterior',
      'Kitchen area full wipe-down',
      'Warehouse dust mopping throughout',
    ];
    const monthlyTasks = ['Refrigerator interior deep clean'];
    const quarterlyTasks = ['Baseboard cleaning — all areas', 'Desk dusting — all offices'];

    const ROW_H   = 0.32;
    const HDR_H   = 0.30;
    const BAND_PAD = 0.08;  // top padding inside band before first row

    // ── WEEKLY BAND ──
    const wRows = Math.max(weeklyLeft.length, weeklyRight.length);
    const wBandH = HDR_H + BAND_PAD + wRows * ROW_H + 0.08;
    const wY = 1.12;

    s.addShape('rect', { x: LM, y: wY, w: CW, h: wBandH, fill: { color: BAND_W }, line: { color: BAND_W } });
    s.addText('WEEKLY', {
      x: LM + 0.14, y: wY + 0.06, w: 1.5, h: 0.20,
      fontSize: 9, bold: true, color: NAVY, fontFace: 'Calibri', charSpacing: 2
    });

    const COL_W2 = (CW - 0.28) / 2;
    const tickX_L = LM + 0.14;
    const textX_L = tickX_L + 0.18;
    const tickX_R = LM + 0.14 + COL_W2 + 0.14;
    const textX_R = tickX_R + 0.18;

    for (let i = 0; i < weeklyLeft.length; i++) {
      const ry = wY + HDR_H + BAND_PAD + i * ROW_H;
      s.addShape('rect', { x: tickX_L, y: ry + 0.04, w: 0.05, h: 0.24, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(weeklyLeft[i], {
        x: textX_L, y: ry + 0.06, w: COL_W2 - 0.22, h: 0.22,
        fontSize: 10, color: DKGRAY, fontFace: 'Calibri'
      });
      s.addText('Weekly', {
        x: textX_L + COL_W2 - 0.88, y: ry + 0.06, w: 0.72, h: 0.22,
        fontSize: 8, italic: true, color: LGRAY, fontFace: 'Calibri', align: 'right'
      });
    }
    for (let i = 0; i < weeklyRight.length; i++) {
      const ry = wY + HDR_H + BAND_PAD + i * ROW_H;
      s.addShape('rect', { x: tickX_R, y: ry + 0.04, w: 0.05, h: 0.24, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(weeklyRight[i], {
        x: textX_R, y: ry + 0.06, w: COL_W2 - 0.22, h: 0.22,
        fontSize: 10, color: DKGRAY, fontFace: 'Calibri'
      });
      s.addText('Weekly', {
        x: textX_R + COL_W2 - 0.88, y: ry + 0.06, w: 0.72, h: 0.22,
        fontSize: 8, italic: true, color: LGRAY, fontFace: 'Calibri', align: 'right'
      });
    }

    // ── MONTHLY BAND ──
    const mY = wY + wBandH + 0.06;
    const mBandH = HDR_H + BAND_PAD + monthlyTasks.length * ROW_H + 0.08;
    s.addShape('rect', { x: LM, y: mY, w: CW, h: mBandH, fill: { color: BAND_M }, line: { color: BAND_M } });
    s.addText('MONTHLY', {
      x: LM + 0.14, y: mY + 0.06, w: 1.5, h: 0.20,
      fontSize: 9, bold: true, color: NAVY, fontFace: 'Calibri', charSpacing: 2
    });
    monthlyTasks.forEach((task, i) => {
      const ry = mY + HDR_H + BAND_PAD + i * ROW_H;
      s.addShape('rect', { x: tickX_L, y: ry + 0.04, w: 0.05, h: 0.24, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(task, {
        x: textX_L, y: ry + 0.06, w: CW - 1.2, h: 0.22,
        fontSize: 10, color: DKGRAY, fontFace: 'Calibri'
      });
      s.addText('Monthly', {
        x: LM + CW - 1.0, y: ry + 0.06, w: 0.72, h: 0.22,
        fontSize: 8, italic: true, color: LGRAY, fontFace: 'Calibri', align: 'right'
      });
    });

    // ── QUARTERLY BAND ──
    const qY = mY + mBandH + 0.06;
    const qBandH = HDR_H + BAND_PAD + quarterlyTasks.length * ROW_H + 0.08;
    s.addShape('rect', { x: LM, y: qY, w: CW, h: qBandH, fill: { color: 'F0F4FF' }, line: { color: 'F0F4FF' } });
    s.addText('QUARTERLY', {
      x: LM + 0.14, y: qY + 0.06, w: 1.8, h: 0.20,
      fontSize: 9, bold: true, color: NAVY, fontFace: 'Calibri', charSpacing: 2
    });
    quarterlyTasks.forEach((task, i) => {
      const ry = qY + HDR_H + BAND_PAD + i * ROW_H;
      s.addShape('rect', { x: tickX_L, y: ry + 0.04, w: 0.05, h: 0.24, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(task, {
        x: textX_L, y: ry + 0.06, w: CW - 1.2, h: 0.22,
        fontSize: 10, color: DKGRAY, fontFace: 'Calibri'
      });
      s.addText('Quarterly', {
        x: LM + CW - 1.0, y: ry + 0.06, w: 0.80, h: 0.22,
        fontSize: 8, italic: true, color: LGRAY, fontFace: 'Calibri', align: 'right'
      });
    });

    // Footer note
    const footY = qY + qBandH + 0.10;
    hl(s, LM, footY, CW);
    s.addText('All frequencies confirmed at onboarding walkthrough with CEO and QA Manager.', {
      x: LM, y: footY + 0.06, w: CW, h: 0.22,
      fontSize: 9, italic: true, color: MGRAY, fontFace: 'Calibri'
    });

    validateSlide('Scope', [
      { name: 'weekly band', y: wY, h: wBandH },
      { name: 'monthly band', y: mY, h: mBandH },
      { name: 'quarterly band', y: qY, h: qBandH },
      { name: 'footer note', y: footY, h: 0.28 }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 5 — YOUR TEAM
  // Layout: three equal columns, circular headshots centered above name/title/bio
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 5, 'YOUR TEAM');

    s.addText('Your Team. Not a Call Center.', {
      x: LM, y: 0.28, w: CW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Three people accountable to your facility — by name, by role, by phone.', {
      x: LM, y: 0.78, w: CW, h: 0.26, fontSize: 12, color: MGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 1.08, CW);

    const COL_W3 = 2.88;
    const team = [
      {
        img: './hereford.png', x: LM,
        name: 'Hereford Johnson',
        creds: 'US Air Force Veteran · SDVOSB · ISSA Member',
        title: 'CEO & Owner',
        stmt: 'Your primary point of contact. Reachable directly by phone — no account managers, no routing, no corporate buffer between you and the person ultimately accountable for every service.'
      },
      {
        img: './victoriana.png', x: 3.56,
        name: 'Victoriana Johnson',
        creds: 'Certified QA Inspector · OrangeQC Platform',
        title: 'QA Manager',
        stmt: 'Conducts weekly on-site inspections, logs every score, and personally owns resolution follow-through on every open service ticket. If a score drops, she is the first to know and the first to respond.'
      },
      {
        img: './johanna.png', x: 6.62,
        name: 'Johanna Hernandez',
        creds: 'Talent Acquisition · Training & Certification',
        title: 'Area Talent Manager',
        stmt: 'Handles recruiting, vetting, background checks, and ongoing training for all custodial staff. Every person assigned to your facility is screened, trained to your environment, and held to documented standards.'
      }
    ];

    team.forEach((t, i) => {
      if (i > 0) vl(s, t.x - 0.14, 1.10, 3.96);
      const cx = t.x + (COL_W3 - 1.10) / 2;
      s.addImage({ path: t.img, x: cx, y: 1.18, w: 1.10, h: 1.10, rounding: true });
      s.addText(t.name, {
        x: t.x, y: 2.36, w: COL_W3, h: 0.30,
        fontSize: 13, bold: true, color: NAVY, fontFace: 'Trebuchet MS', align: 'center'
      });
      s.addText(t.creds, {
        x: t.x, y: 2.68, w: COL_W3, h: 0.30,
        fontSize: 9, color: LGRAY, fontFace: 'Calibri', align: 'center', wrap: true
      });
      s.addText(t.title, {
        x: t.x, y: 3.00, w: COL_W3, h: 0.26,
        fontSize: 11, bold: true, color: PROSPECT, fontFace: 'Calibri', align: 'center'
      });
      hl(s, t.x, 3.30, COL_W3);
      s.addText(t.stmt, {
        x: t.x, y: 3.38, w: COL_W3, h: 1.26,
        fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true
      });
    });

    hl(s, LM, 4.72, CW);
    s.addText('"I\'ve held the mop. I\'ve been the crew. That\'s why we\'re built around accountability, not excuses." — Hereford Johnson, CEO', {
      x: LM, y: 4.78, w: CW, h: 0.24,
      fontSize: 10, italic: true, color: MGRAY, fontFace: 'Calibri'
    });

    validateSlide('Team', [
      { name: 'headshots', y: 1.18, h: 1.10 },
      { name: 'bios', y: 3.38, h: 1.26 },
      { name: 'pullquote', y: 4.78, h: 0.24 }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 6 — QUALITY ASSURANCE
  // Layout: left 42% three stacked feature rows, right 54% three large stats
  //         ONE vertical hairline rule at x=4.4"
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 6, 'QUALITY ASSURANCE');

    s.addText('You Get Full Visibility Into Every Clean.', {
      x: LM, y: 0.28, w: CW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hl(s, LM, 0.84, CW);

    const LZ_W = 3.72;  // left zone width
    const RX6  = 4.52;  // right zone x
    const RW6  = RM - RX6;  // 5.08"

    // Left: intro + three feature rows
    s.addText(
      'Every MDF service is backed by a mobile inspection and ticketing platform that gives you real-time visibility into your facility. ' +
      'This is not an internal tool — it is client-facing accountability. You receive access to your own dashboard.',
      {
        x: LM, y: 0.96, w: LZ_W, h: 0.88,
        fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true
      }
    );
    hl(s, LM, 1.90, LZ_W);

    const features = [
      {
        label: 'Inspection Scoring',
        desc: 'Every area is graded at each visit. Scores trend over time — you can see at a glance whether standards are holding or slipping, week over week.'
      },
      {
        label: 'Service Ticket System',
        desc: 'Any flagged issue auto-creates a ticket, assigned to a team member and time-stamped. Resolution is tracked from open to close — nothing disappears.'
      },
      {
        label: 'Full Audit Trail',
        desc: 'Every service, every score, every resolved ticket lives in your dashboard. Useful for compliance reviews, facility audits, and ongoing accountability records.'
      },
    ];
    const FEAT_H = 0.94;
    features.forEach((f, i) => {
      const fy = 1.98 + i * FEAT_H;
      s.addText(f.label, {
        x: LM, y: fy, w: LZ_W, h: 0.26,
        fontSize: 12, bold: true, color: DKGRAY, fontFace: 'Trebuchet MS'
      });
      s.addText(f.desc, {
        x: LM, y: fy + 0.30, w: LZ_W, h: 0.52,
        fontSize: 10.5, color: MGRAY, fontFace: 'Calibri', wrap: true
      });
      if (i < features.length - 1) hl(s, LM, fy + FEAT_H - 0.06, LZ_W);
    });

    hl(s, LM, 4.86, LZ_W);
    s.addText('Included with every MDF contract — at no additional charge.', {
      x: LM, y: 4.92, w: LZ_W, h: 0.20,
      fontSize: 10.5, italic: true, color: GREEN, fontFace: 'Calibri'
    });

    // Single vertical hairline
    vl(s, 4.42, 0.84, 4.24);

    // Right: 3 large stats stacked
    const QC_STATS = [
      { stat: '90%+', label: 'TARGET INSPECTION SCORE', sub: 'Tracked and reported every week' },
      { stat: '<2hr', label: 'AVERAGE RESPONSE TIME',   sub: 'Ticket open to acknowledgment' },
      { stat: '<24hr', label: 'AVERAGE RESOLUTION TIME', sub: 'Issue flagged to issue closed' },
    ];
    const STAT_H6 = 1.38;
    QC_STATS.forEach((st, i) => {
      const sy = 0.94 + i * STAT_H6;
      s.addText(st.label, {
        x: RX6, y: sy, w: RW6, h: 0.20,
        fontSize: 7.5, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 2.5
      });
      s.addText(st.stat, {
        x: RX6, y: sy + 0.22, w: RW6, h: 0.82,
        fontSize: 48, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
      });
      s.addText(st.sub, {
        x: RX6, y: sy + 1.06, w: RW6, h: 0.24,
        fontSize: 10, color: MGRAY, fontFace: 'Calibri'
      });
      if (i < QC_STATS.length - 1) hl(s, RX6, sy + STAT_H6 - 0.04, RW6);
    });

    validateSlide('QC', [
      { name: 'features', y: 1.98, h: features.length * FEAT_H },
      { name: 'stats', y: 0.94, h: QC_STATS.length * STAT_H6 },
      { name: 'included', y: 4.92, h: 0.20 }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 7 — RAMP-UP PLAN
  // Layout: full-width Gantt table, no column split
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 7, 'RAMP-UP PLAN');

    s.addText('Your Ramp-Up. Before Day One.', {
      x: LM, y: 0.28, w: CW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    hl(s, LM, 0.84, CW);

    const GX     = LM;
    const GY     = 0.92;
    const LAB_W  = 3.10;
    const N_COLS = 6;
    const COL_WG = (CW - LAB_W) / N_COLS;  // ~1.0"
    const ROW_HG = 0.46;
    const COL_LABELS = ['Wk -2', 'Wk -1', 'Week 1', 'Week 2', 'Mo. 2', 'Mo. 3'];

    // Header row
    s.addShape('rect', { x: GX, y: GY, w: LAB_W, h: ROW_HG, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText('ACTIVITY', {
      x: GX + 0.12, y: GY + 0.13, w: LAB_W, h: 0.22,
      fontSize: 8, bold: true, color: GOLD, fontFace: 'Calibri', charSpacing: 2
    });
    COL_LABELS.forEach((lbl, c) => {
      const cx = GX + LAB_W + c * COL_WG;
      s.addShape('rect', { x: cx, y: GY, w: COL_WG, h: ROW_HG, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText(lbl, {
        x: cx, y: GY + 0.13, w: COL_WG, h: 0.22,
        fontSize: 9, color: LGRAY, fontFace: 'Calibri', align: 'center'
      });
    });

    const activities = [
      { name: 'CEO + QA Manager Site Walk',    bars: [0, 1], color: GOLD  },
      { name: 'Key Handoff & Supply Staging',  bars: [0, 1], color: GOLD  },
      { name: 'Team Assignment & Orientation', bars: [1],    color: GOLD  },
      { name: 'Service Launch',                bars: [2],    color: NAVY  },
      { name: 'Daily Supervisor Check-Ins',    bars: [2, 3], color: NAVY  },
      { name: 'OrangeQC Baseline Report',      bars: [2, 3], color: NAVY  },
      { name: '30-Day Review Call',            bars: [4],    color: '2E6B3E' },
      { name: '90-Day QBR & Scope Review',     bars: [5],    color: '2E6B3E' },
    ];

    activities.forEach((act, i) => {
      const ry = GY + ROW_HG + i * ROW_HG;
      const rowBg = i % 2 === 0 ? WHITE : 'F4F7FB';
      s.addShape('rect', { x: GX, y: ry, w: LAB_W, h: ROW_HG, fill: { color: rowBg }, line: { color: RULE } });
      s.addText(act.name, {
        x: GX + 0.12, y: ry + 0.13, w: LAB_W - 0.16, h: 0.22,
        fontSize: 10, color: DKGRAY, fontFace: 'Calibri'
      });
      for (let c = 0; c < N_COLS; c++) {
        const cx = GX + LAB_W + c * COL_WG;
        s.addShape('rect', { x: cx, y: ry, w: COL_WG, h: ROW_HG, fill: { color: rowBg }, line: { color: RULE } });
      }
      if (act.bars.length > 0) {
        const bx = GX + LAB_W + act.bars[0] * COL_WG + 0.06;
        const bw = (act.bars[act.bars.length - 1] - act.bars[0] + 1) * COL_WG - 0.12;
        s.addShape('rect', {
          x: bx, y: ry + 0.10, w: bw, h: ROW_HG * 0.55,
          fill: { color: act.color }, line: { color: act.color }
        });
      }
    });

    const legY = GY + ROW_HG * (1 + activities.length) + 0.10;
    [[GOLD, 'Pre-Start'], [NAVY, 'Active Service'], ['2E6B3E', 'Milestone Review']].forEach(([c, lbl], i) => {
      const lx = LM + i * 3.0;
      s.addShape('rect', { x: lx, y: legY, w: 0.24, h: 0.16, fill: { color: c }, line: { color: c } });
      s.addText(lbl, {
        x: lx + 0.32, y: legY - 0.01, w: 2.5, h: 0.18,
        fontSize: 9, color: MGRAY, fontFace: 'Calibri'
      });
    });

    const ganttBottom = GY + ROW_HG * (1 + activities.length);
    validateSlide('Gantt', [
      { name: 'gantt table', y: GY, h: ROW_HG * (1 + activities.length) },
      { name: 'legend', y: legY, h: 0.18 }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 8 — SOCIAL PROOF
  // Layout: full-width hero quote (top), two secondary quotes side-by-side (mid),
  //         right logo strip with real images — horizontal rules separate zones
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 8, 'CLIENT TESTIMONIALS');

    s.addText('What Our Clients Say.', {
      x: LM, y: 0.28, w: CW, h: 0.50, fontSize: 24, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('Facilities that can\'t afford to get it wrong — and don\'t.', {
      x: LM, y: 0.78, w: CW, h: 0.26, fontSize: 12, color: MGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 1.08, CW);

    // Vertical hairline separating quotes from logo strip
    const LOGO_X = 7.72;
    const LOGO_W = RM - LOGO_X;  // 1.88"
    const QUOTE_W = LOGO_X - LM - 0.14;  // 7.08"
    vl(s, LOGO_X, 1.10, 3.96);

    // ── TOP ZONE: hero quote (y=1.14 to ~2.90) ──
    s.addText(
      '"What impressed us most was their understanding of our compliance requirements. They didn\'t just clean — ' +
      'they followed our protocols, documented everything, and worked around our production schedule without missing a beat."',
      {
        x: LM, y: 1.14, w: QUOTE_W, h: 1.14,
        fontSize: 13, italic: true, color: NAVY, fontFace: 'Georgia', wrap: true
      }
    );
    s.addText('— Manufacturing Plant Operations Manager', {
      x: LM, y: 2.30, w: QUOTE_W, h: 0.24,
      fontSize: 9.5, color: LGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 2.60, QUOTE_W);

    // ── MIDDLE ZONE: two secondary quotes (y=2.66 to ~3.82) ──
    const Q_W2 = (QUOTE_W - 0.20) / 2;

    s.addText('"The team at MDF understands that in our environment, cleaning is part of our safety program — not just an afterthought."', {
      x: LM, y: 2.70, w: Q_W2, h: 0.72,
      fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Sheriff\'s Office Facility Manager', {
      x: LM, y: 3.44, w: Q_W2, h: 0.20,
      fontSize: 9, color: LGRAY, fontFace: 'Calibri'
    });

    s.addText('"We\'ve worked with several cleaning companies over the years, but Mad Dog is different. When there\'s an issue, they fix it immediately."', {
      x: LM + Q_W2 + 0.20, y: 2.70, w: Q_W2, h: 0.72,
      fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Government Administrator', {
      x: LM + Q_W2 + 0.20, y: 3.44, w: Q_W2, h: 0.20,
      fontSize: 9, color: LGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 3.72, QUOTE_W);

    // ── BOTTOM ZONE: third quote (y=3.78 to ~4.9) ──
    s.addText('"The background checks and professionalism of their crew gave us confidence from day one. In a government facility, security and accountability aren\'t negotiable. Mad Dog gets that."', {
      x: LM, y: 3.80, w: QUOTE_W, h: 0.82,
      fontSize: 10.5, italic: true, color: MGRAY, fontFace: 'Calibri', wrap: true
    });
    s.addText('— Municipal Building Supervisor', {
      x: LM, y: 4.64, w: QUOTE_W, h: 0.20,
      fontSize: 9, color: LGRAY, fontFace: 'Calibri'
    });

    // ── LOGO STRIP: FAA, Army, ISSA stacked ──
    const logos = [
      { path: './logo_faa.png',  label: 'Certified Past Performance', y: 1.22 },
      { path: './logo_army.png', label: 'Past Performance',           y: 2.62 },
      { path: './logo_issa.png', label: 'Industry Member',            y: 4.02 },
    ];
    logos.forEach(lg => {
      s.addImage({
        path: lg.path,
        x: LOGO_X + 0.12, y: lg.y, w: LOGO_W - 0.24, h: 0.80,
        sizing: { type: 'contain', w: LOGO_W - 0.24, h: 0.80 }
      });
      s.addText(lg.label, {
        x: LOGO_X + 0.08, y: lg.y + 0.86, w: LOGO_W - 0.16, h: 0.20,
        fontSize: 7, color: LGRAY, fontFace: 'Calibri', align: 'center'
      });
    });

    validateSlide('Social Proof', [
      { name: 'hero quote', y: 1.14, h: 1.14 },
      { name: 'secondary quotes', y: 2.70, h: 0.92 },
      { name: 'third quote', y: 3.80, h: 0.82 },
      { name: 'attribution 3', y: 4.64, h: 0.20 }
    ]);
  }

  // ════════════════════════════════════════════════════════════════════════════
  // SLIDE 9 — INVESTMENT + NEXT STEPS
  // Layout: left 52% pricing table, right 44% next steps — the one split slide
  // ════════════════════════════════════════════════════════════════════════════
  {
    const s = prs.addSlide();
    s.background = { color: WHITE };
    addChrome(s, prs, 9, 'YOUR INVESTMENT & NEXT STEPS');

    const LH = 4.92;   // left half width
    const RX9 = 5.20;  // right half x start
    const RW9 = RM - RX9;  // 4.40"

    // ── LEFT HALF ──
    s.addText('YOUR INVESTMENT', {
      x: LM, y: 0.26, w: LH, h: 0.20,
      fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('$1,000', {
      x: LM, y: 0.46, w: LH, h: 1.00,
      fontSize: 58, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('per month  ·  $12,000 annually  ·  Month-to-Month  ·  30-Day Notice', {
      x: LM, y: 1.46, w: LH, h: 0.24,
      fontSize: 9.5, color: MGRAY, fontFace: 'Calibri'
    });
    hl(s, LM, 1.76, LH);

    const items = [
      { label: 'Labor — W-2 Employees',       value: '$630',     green: false },
      { label: 'Supplies & Consumables (4%)', value: '$40',      green: false },
      { label: 'Equipment & Maintenance (3%)', value: '$30',      green: false },
      { label: 'QA Inspection Reports',       value: 'Included', green: true  },
      { label: 'Dedicated QA Manager',        value: 'Included', green: true  },
      { label: 'Ownership Direct Line',       value: 'Included', green: true  },
    ];
    const ITEM_H = 0.38;
    items.forEach((item, i) => {
      const iy = 1.84 + i * ITEM_H;
      const bg = i % 2 === 0 ? WHITE : 'F4F7FB';
      s.addShape('rect', { x: LM - 0.02, y: iy, w: LH + 0.04, h: ITEM_H, fill: { color: bg }, line: { color: bg } });
      s.addText(item.label, {
        x: LM + 0.10, y: iy + 0.08, w: LH - 1.4, h: 0.24,
        fontSize: 10, color: MGRAY, fontFace: 'Calibri'
      });
      s.addText(item.value, {
        x: LM + LH - 1.35, y: iy + 0.08, w: 1.25, h: 0.24,
        fontSize: 10, bold: true, color: item.green ? GREEN : DKGRAY,
        fontFace: 'Calibri', align: 'right'
      });
    });

    const totY = 1.84 + items.length * ITEM_H + 0.06;
    s.addShape('rect', { x: LM - 0.02, y: totY, w: LH + 0.04, h: 0.44, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText('Monthly Total', {
      x: LM + 0.10, y: totY + 0.10, w: LH - 1.8, h: 0.26,
      fontSize: 12, bold: true, color: WHITE, fontFace: 'Trebuchet MS'
    });
    s.addText('$1,000', {
      x: LM + LH - 1.6, y: totY + 0.10, w: 1.5, h: 0.26,
      fontSize: 12, bold: true, color: GOLD, fontFace: 'Trebuchet MS', align: 'right'
    });

    vl(s, RX9 - 0.12, 0.22, 5.00);

    // ── RIGHT HALF ──
    s.addText('READY TO MOVE FORWARD?', {
      x: RX9, y: 0.26, w: RW9, h: 0.20,
      fontSize: 7, bold: true, color: LGRAY, fontFace: 'Calibri', charSpacing: 3.5
    });
    s.addText('What happens when you say yes:', {
      x: RX9, y: 0.48, w: RW9, h: 0.56,
      fontSize: 20, bold: true, color: NAVY, fontFace: 'Trebuchet MS', wrap: true
    });

    const steps = [
      'Agreement signed & start date confirmed',
      'CEO + QA Manager schedule facility site walk',
      'Team assigned, keys exchanged, supplies staged',
      'Inspection dashboard created — you get login access',
      'First service delivered on your start date, July 1',
    ];
    const STEP_H = 0.58;
    steps.forEach((step, i) => {
      const sy = 1.14 + i * STEP_H;
      s.addText(String(i + 1), {
        x: RX9, y: sy, w: 0.34, h: 0.34,
        fontSize: 16, bold: true, color: GOLD, fontFace: 'Trebuchet MS'
      });
      hl(s, RX9, sy + 0.38, 0.34, GOLD);
      s.addText(step, {
        x: RX9 + 0.44, y: sy + 0.04, w: RW9 - 0.44, h: 0.42,
        fontSize: 11, color: MGRAY, fontFace: 'Calibri', wrap: true
      });
    });

    hl(s, RX9, 4.08, RW9);
    s.addText('Hereford Johnson', {
      x: RX9, y: 4.18, w: RW9, h: 0.30,
      fontSize: 13, bold: true, color: NAVY, fontFace: 'Trebuchet MS'
    });
    s.addText('623-321-2542  ·  office@maddogcleaning.com', {
      x: RX9, y: 4.50, w: RW9, h: 0.24,
      fontSize: 10.5, color: MGRAY, fontFace: 'Calibri'
    });

    validateSlide('Investment', [
      { name: 'price', y: 0.46, h: 1.00 },
      { name: 'line items', y: 1.84, h: items.length * ITEM_H },
      { name: 'total bar', y: totY, h: 0.44 },
      { name: 'steps', y: 1.14, h: steps.length * STEP_H },
      { name: 'contact', y: 4.50, h: 0.24 }
    ]);
  }

  await prs.writeFile({ fileName: 'MDF_Proposal_LogicalSystems_2026-05-28.pptx' });
  console.log('Saved: MDF_Proposal_LogicalSystems_2026-05-28.pptx');
}

build().catch(err => { console.error(err); process.exit(1); });
