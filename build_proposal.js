const PptxGenJS = require('pptxgenjs');

// ─── PALETTE (no # prefix) ───────────────────────────────────────────────────
const NAVY  = "0D1F3C";
const WHITE = "FFFFFF";
const MGRAY = "6B7280";
const LGRAY = "9CA3AF";
const DGRAY = "374151";
const RULE  = "E5E7EB";
const GREEN = "2E7D52";
const PROSPECT_HEX = "1B3A6B";

// ─── DATA ────────────────────────────────────────────────────────────────────
const PROSPECT_NAME       = "Logical Systems Inc.";
const PROSPECT_NAME_SHORT = "Logical Systems";
const CONTACT_NAME        = "April Bocox";
const CONTACT_TITLE       = "Health and Safety Coordinator";
const PROPOSAL_DATE       = "May 28, 2026";
const START_DATE          = "July 1, 2026";
const CONTRACT_TERM       = "Month-to-Month  ·  30-Day Notice";
const FREQUENCY           = "Weekly";
const MONTHLY_REVENUE     = 1000;
const ANNUAL_REVENUE      = 12000;
const LABOR               = 630;
const SUPPLIES            = 40;
const EQUIP               = 30;

const INDUSTRY_TYPE      = "Manufacturing / Automation Controls";
const FACILITY_PROFILE   = "Controls Integrator Since 1985";
const COMPLIANCE_CONTEXT = "OSHA / Production-Grade";

const PARA_1 = "LSI operates manufacturing and industrial facilities where precision, compliance, and uptime are non-negotiable. Your environment demands cleaning that works around production schedules, protects sensitive controls equipment, and meets the documentation standards your own clients hold you to.";
const PARA_2 = "MDF delivers compliance-ready facility services designed for automation and controls environments. We coordinate around your production calendar, document every service, and treat your facility with the same operational discipline your team applies to every project. When we say nothing gets missed, we have the inspection scores and service tickets to back it up.";
const VALUES_QUOTE = "Your core values — service, integrity, and excellence — are the same values we build our teams around. That alignment isn't coincidental. It's why this partnership works.";

const WEEKLY_TASKS = [
  { name: "Restrooms (3): sanitize & disinfect all fixtures" },
  { name: "Restrooms: mop & disinfect floors, clean mirrors" },
  { name: "Office mopping, sweeping & vacuuming" },
  { name: "General dusting — all areas" },
  { name: "Front glass cleaning" },
  { name: "Break room countertops, tables & chairs" },
  { name: "Microwave — inside & outside" },
  { name: "Refrigerator & water machine exterior" },
  { name: "Kitchen area full wipe-down" },
  { name: "Warehouse dust mopping throughout" },
];
const MONTHLY_TASKS = [
  { name: "Refrigerator interior deep clean" },
];
const QUARTERLY_TASKS = [
  { name: "Baseboard cleaning — all areas" },
  { name: "Desk dusting — all offices" },
];

const HERO_QUOTE  = "What impressed us most was their understanding of our compliance requirements. They didn't just clean — they followed our protocols, documented everything, and worked around our production schedule without missing a beat.";
const HERO_SOURCE = "Manufacturing Plant Operations Manager";
const QUOTE2      = "The team at MDF understands that in our environment, cleaning is part of our safety program — not just an afterthought.";
const SOURCE2     = "Sheriff's Office Facility Manager";
const QUOTE3      = "We've worked with several cleaning companies over the years, but Mad Dog is different. When there's an issue, they fix it immediately.";
const SOURCE3     = "Government Administrator";
const QUOTE4      = "The background checks and professionalism of their crew gave us confidence from day one. In a government facility, security and accountability aren't negotiable. Mad Dog gets that.";
const SOURCE4     = "Municipal Building Supervisor";

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function slideHeader(pres, s, sectionLabel, pageNum) {
  s.addShape('rect', {
    x: 0, y: 0, w: 10, h: 0.055, fill: { color: NAVY }, line: { color: NAVY }
  });
  s.addText(sectionLabel.toUpperCase(), {
    x: 0.45, y: 0.10, w: 6, h: 0.18,
    fontSize: 7, fontFace: 'Calibri', bold: true, color: LGRAY, charSpacing: 3.5, margin: 0
  });
  s.addText(String(pageNum), {
    x: 9.3, y: 0.10, w: 0.55, h: 0.18,
    fontSize: 8, fontFace: 'Calibri', color: LGRAY, align: 'right', margin: 0
  });
}

function hRule(pres, s, x, y, w, color) {
  s.addShape('rect', {
    x, y, w, h: 0.018, fill: { color: color || RULE }, line: { color: color || RULE }
  });
}

function vRule(pres, s, x, y, h, color) {
  s.addShape('rect', {
    x, y, w: 0.018, h, fill: { color: color || RULE }, line: { color: color || RULE }
  });
}

function logoMDF(s) {
  s.addImage({
    path: './mdf_logo_white.png', x: 8.55, y: 4.95, w: 1.1, h: 0.55,
    sizing: { type: 'contain', w: 1.1, h: 0.55 }
  });
}

// ─── BUILD ────────────────────────────────────────────────────────────────────
async function build() {
  const pres = new PptxGenJS();
  pres.layout = 'LAYOUT_WIDE';

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 1 — COVER
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { path: './cover.jpg' };

    s.addImage({
      path: './mdf_logo_all_white.png',
      x: 0.42, y: 0.30, w: 1.05, h: 0.65,
      sizing: { type: 'contain', w: 1.05, h: 0.65 }
    });

    s.addText('PREPARED FOR', {
      x: 0.45, y: 3.52, w: 5, h: 0.20,
      fontSize: 7, fontFace: 'Calibri', bold: true,
      color: 'A8B8CC', charSpacing: 3.5, margin: 0
    });
    s.addText(PROSPECT_NAME, {
      x: 0.45, y: 3.78, w: 7.5, h: 1.05,
      fontSize: 34, fontFace: 'Trebuchet MS', bold: true,
      color: WHITE, margin: 0, lineSpacingMultiple: 1.05
    });
    s.addShape('rect', {
      x: 0.45, y: 4.90, w: 4.0, h: 0.018,
      fill: { color: '5A6A7A' }, line: { color: '5A6A7A' }
    });
    s.addText(`Facility Services Proposal  ·  ${CONTACT_NAME}, ${CONTACT_TITLE}  ·  ${PROPOSAL_DATE}`, {
      x: 0.45, y: 4.98, w: 9.1, h: 0.26,
      fontSize: 9, fontFace: 'Calibri', color: '8B9BAD', margin: 0
    });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 2 — WHY MDF
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Why Mad Dog Facility Partners', 2);

    s.addText('You can choose any janitorial company.', {
      x: 0.45, y: 0.38, w: 9.1, h: 0.48,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    s.addText('Here is why our clients stay for an average of 6 years.', {
      x: 0.45, y: 0.88, w: 8, h: 0.28,
      fontSize: 12, fontFace: 'Calibri', color: MGRAY, margin: 0
    });
    hRule(pres, s, 0.45, 1.24, 9.1);

    const cols = [
      {
        stat: '92%+', sub: 'avg. inspection score', head: 'Real-Time Quality Assurance',
        body: 'Every service tracked through a third-party inspection platform — GPS-logged, photo-documented, time-stamped. Scores shared with you after every visit. You never have to wonder if the work was done or how well.'
      },
      {
        stat: '<24hr', sub: 'avg. resolution time', head: 'Documented Service Resolution',
        body: 'Every flagged issue becomes a service ticket with photos, notes, and an assigned owner. Tracked from open to close. Nothing falls through — every response documented and time-stamped.'
      },
      {
        stat: 'CEO', sub: 'is your primary contact', head: 'Direct Executive Access',
        body: 'Hereford Johnson, US Air Force veteran and company founder, picks up the phone. No account managers, no call routing, no corporate layers between you and the person accountable for every service.'
      },
    ];

    cols.forEach((col, i) => {
      const cx = 0.45 + i * 3.07;

      s.addText(col.stat, {
        x: cx, y: 1.42, w: 2.9, h: 0.82,
        fontSize: 42, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
      });
      s.addText(col.sub, {
        x: cx, y: 2.24, w: 2.9, h: 0.22,
        fontSize: 8.5, fontFace: 'Calibri', color: LGRAY, margin: 0
      });
      hRule(pres, s, cx, 2.52, 2.8);
      s.addText(col.head, {
        x: cx, y: 2.65, w: 2.9, h: 0.45,
        fontSize: 12, fontFace: 'Trebuchet MS', bold: true, color: DGRAY, margin: 0, lineSpacingMultiple: 1.1
      });
      s.addText(col.body, {
        x: cx, y: 3.14, w: 2.9, h: 1.55,
        fontSize: 10.5, fontFace: 'Calibri', color: MGRAY, margin: 0
      });

      if (i < 2) vRule(pres, s, cx + 2.95, 1.42, 3.28);
    });

    hRule(pres, s, 0.45, 4.74, 9.1);
    s.addText('"We surveyed our clients on what we should do more of. The #1 answer was communication and integrity. We believe this is why our average client has been with us for 6 years."', {
      x: 0.45, y: 4.82, w: 7.8, h: 0.42,
      fontSize: 9.5, fontFace: 'Calibri', italic: true, color: MGRAY, margin: 0
    });
    logoMDF(s);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 3 — YOUR FACILITY
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Your Facility', 3);

    s.addText(`We built this for ${PROSPECT_NAME_SHORT}.`, {
      x: 0.45, y: 0.38, w: 5.4, h: 0.72,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.05
    });
    hRule(pres, s, 0.45, 1.18, 5.3);

    s.addText(PARA_1, {
      x: 0.45, y: 1.32, w: 5.3, h: 0.95,
      fontSize: 10.5, fontFace: 'Calibri', color: MGRAY, margin: 0, lineSpacingMultiple: 1.4
    });
    s.addText(PARA_2, {
      x: 0.45, y: 2.35, w: 5.3, h: 0.95,
      fontSize: 10.5, fontFace: 'Calibri', color: MGRAY, margin: 0, lineSpacingMultiple: 1.4
    });

    hRule(pres, s, 0.45, 3.42, 5.3);
    s.addText(`"${VALUES_QUOTE}"`, {
      x: 0.45, y: 3.55, w: 5.3, h: 0.65,
      fontSize: 11, fontFace: 'Calibri', italic: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.3
    });
    s.addText('— Hereford Johnson, CEO, Mad Dog Facility Partners', {
      x: 0.45, y: 4.26, w: 5.3, h: 0.22,
      fontSize: 9, fontFace: 'Calibri', color: LGRAY, margin: 0
    });

    vRule(pres, s, 6.1, 0.38, 4.7);

    const facts = [
      { label: 'INDUSTRY TYPE',      value: INDUSTRY_TYPE },
      { label: 'FACILITY PROFILE',   value: FACILITY_PROFILE },
      { label: 'COMPLIANCE CONTEXT', value: COMPLIANCE_CONTEXT },
    ];
    facts.forEach((f, i) => {
      const fy = 0.45 + i * 1.52;
      s.addText(f.label, {
        x: 6.3, y: fy, w: 3.25, h: 0.20,
        fontSize: 7, fontFace: 'Calibri', bold: true, color: LGRAY, charSpacing: 3, margin: 0
      });
      s.addText(f.value, {
        x: 6.3, y: fy + 0.24, w: 3.25, h: 0.82,
        fontSize: 18, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.05
      });
      if (i < 2) hRule(pres, s, 6.3, fy + 1.38, 3.2);
    });

    logoMDF(s);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 4 — SCOPE (frequency bands, no addTable)
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Scope of Work', 4);

    s.addText('Your Facility. Your Scope.', {
      x: 0.45, y: 0.38, w: 8, h: 0.46,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    s.addText(`Weekly service  ·  Start July 1, 2026  ·  ${CONTRACT_TERM}`, {
      x: 0.45, y: 0.88, w: 8, h: 0.24,
      fontSize: 10.5, fontFace: 'Calibri', color: MGRAY, margin: 0
    });
    hRule(pres, s, 0.45, 1.18, 9.1);

    const bands = [
      { label: 'WEEKLY',    fill: 'F0F4FF', tasks: WEEKLY_TASKS },
      { label: 'MONTHLY',   fill: 'F4F7FB', tasks: MONTHLY_TASKS },
      { label: 'QUARTERLY', fill: 'F8F9FA', tasks: QUARTERLY_TASKS },
    ].filter(b => b.tasks && b.tasks.length > 0);

    const totalBandH = 3.48;
    const bandH = totalBandH / bands.length;
    const bandY0 = 1.24;

    bands.forEach((band, bi) => {
      const by = bandY0 + bi * bandH;

      s.addShape('rect', {
        x: 0.45, y: by, w: 9.1, h: bandH,
        fill: { color: band.fill }, line: { color: 'E5E7EB' }
      });
      s.addText(band.label, {
        x: 0.62, y: by + 0.10, w: 1.5, h: 0.22,
        fontSize: 7.5, fontFace: 'Calibri', bold: true, color: NAVY, charSpacing: 2, margin: 0
      });
      hRule(pres, s, 0.62, by + 0.34, 8.75, 'D1D5DB');

      const half = Math.ceil(band.tasks.length / 2);
      const leftTasks  = band.tasks.slice(0, half);
      const rightTasks = band.tasks.slice(half);
      const rowH = (bandH - 0.45) / Math.max(half, 1);
      const freqLabel = band.label.charAt(0) + band.label.slice(1).toLowerCase();

      leftTasks.forEach((task, ti) => {
        const ty = by + 0.42 + ti * rowH;
        s.addShape('rect', {
          x: 0.62, y: ty + 0.04, w: 0.04, h: 0.22,
          fill: { color: NAVY }, line: { color: NAVY }
        });
        s.addText(task.name, {
          x: 0.76, y: ty, w: 3.5, h: 0.28,
          fontSize: 10, fontFace: 'Calibri', color: DGRAY, margin: 0
        });
        s.addText(task.freq || freqLabel, {
          x: 4.10, y: ty, w: 0.80, h: 0.28,
          fontSize: 8.5, fontFace: 'Calibri', italic: true, color: LGRAY, align: 'right', margin: 0
        });
      });

      rightTasks.forEach((task, ti) => {
        const ty = by + 0.42 + ti * rowH;
        s.addShape('rect', {
          x: 5.10, y: ty + 0.04, w: 0.04, h: 0.22,
          fill: { color: NAVY }, line: { color: NAVY }
        });
        s.addText(task.name, {
          x: 5.24, y: ty, w: 3.5, h: 0.28,
          fontSize: 10, fontFace: 'Calibri', color: DGRAY, margin: 0
        });
        s.addText(task.freq || freqLabel, {
          x: 8.65, y: ty, w: 0.90, h: 0.28,
          fontSize: 8.5, fontFace: 'Calibri', italic: true, color: LGRAY, align: 'right', margin: 0
        });
      });
    });

    s.addText('All frequencies confirmed at onboarding walkthrough with CEO and QA Manager.', {
      x: 0.45, y: 4.80, w: 7.5, h: 0.22,
      fontSize: 9, fontFace: 'Calibri', italic: true, color: LGRAY, margin: 0
    });
    logoMDF(s);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 5 — TEAM
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Your Team', 5);

    s.addText('Your Team. Not a Call Center.', {
      x: 0.45, y: 0.38, w: 9, h: 0.48,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    s.addText('Three people accountable to your facility — by name, by role, by phone.', {
      x: 0.45, y: 0.88, w: 8, h: 0.28,
      fontSize: 12, fontFace: 'Calibri', color: MGRAY, margin: 0
    });
    hRule(pres, s, 0.45, 1.22, 9.1);

    const members = [
      {
        img: './hereford.png', name: 'Hereford Johnson',
        creds: 'US Air Force Veteran  ·  SDVOSB  ·  ISSA Member',
        title: 'CEO & Owner', titleColor: NAVY,
        bio: 'Your primary point of contact. Picks up the phone personally — no account managers, no call routing, no corporate layers between you and the person accountable for every service.'
      },
      {
        img: './victoriana.png', name: 'Victoriana Johnson',
        creds: 'Certified QA Inspector  ·  OrangeQC Platform',
        title: 'QA Manager', titleColor: PROSPECT_HEX,
        bio: 'Conducts weekly on-site inspections and logs every score. Personally owns resolution follow-through on every open service ticket. If a score drops, she is first to know and first to respond.'
      },
      {
        img: './johanna.png', name: 'Johanna Hernandez',
        creds: 'Talent Acquisition  ·  Training & Certification',
        title: 'Area Talent Manager', titleColor: GREEN,
        bio: 'Handles recruiting, vetting, background checks, and ongoing training for all custodial staff. Every person assigned to your facility is screened, trained to your environment, and held to documented standards.'
      },
    ];

    members.forEach((m, i) => {
      const cx = 0.45 + i * 3.07;
      const imgX = cx + (2.9 / 2) - 0.55;

      s.addImage({
        path: m.img,
        x: imgX, y: 1.38, w: 1.10, h: 1.10,
        rounding: true,
        sizing: { type: 'cover', w: 1.10, h: 1.10 }
      });

      s.addText(m.name, {
        x: cx, y: 2.58, w: 2.9, h: 0.36,
        fontSize: 13, fontFace: 'Trebuchet MS', bold: true, color: NAVY, align: 'center', margin: 0
      });
      s.addText(m.creds, {
        x: cx, y: 2.95, w: 2.9, h: 0.24,
        fontSize: 8.5, fontFace: 'Calibri', color: LGRAY, align: 'center', margin: 0
      });
      s.addText(m.title, {
        x: cx, y: 3.22, w: 2.9, h: 0.26,
        fontSize: 10, fontFace: 'Calibri', bold: true, color: m.titleColor, align: 'center', margin: 0
      });
      hRule(pres, s, cx, 3.52, 2.8);
      s.addText(m.bio, {
        x: cx, y: 3.64, w: 2.9, h: 1.12,
        fontSize: 10, fontFace: 'Calibri', color: MGRAY, margin: 0, lineSpacingMultiple: 1.3
      });

      if (i < 2) vRule(pres, s, cx + 2.95, 1.38, 3.38);
    });

    hRule(pres, s, 0.45, 4.82, 9.1);
    s.addText('"I\'ve held the mop. I\'ve been the crew. That\'s why we\'re built around accountability, not excuses." — Hereford Johnson, CEO', {
      x: 0.45, y: 4.90, w: 7.8, h: 0.30,
      fontSize: 9, fontFace: 'Calibri', italic: true, color: MGRAY, margin: 0
    });
    logoMDF(s);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 6 — QUALITY / ORANGEQC
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Quality Assurance', 6);

    s.addText('You Get Full Visibility Into Every Clean.', {
      x: 0.45, y: 0.38, w: 9.1, h: 0.48,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    hRule(pres, s, 0.45, 0.94, 9.1);

    const features = [
      {
        head: 'Inspection Scoring',
        body: 'Every zone graded at each visit. Scores trend over time — you see at a glance whether standards are holding or slipping, week over week.'
      },
      {
        head: 'Service Ticket System',
        body: 'Any flagged issue auto-creates a ticket, assigned to a team member and time-stamped. Resolution tracked from open to close. Nothing disappears.'
      },
      {
        head: 'Full Audit Trail',
        body: 'Every service, every score, every resolved ticket lives in your dashboard. Useful for compliance reviews, facility audits, and accountability records.'
      },
    ];

    const featureH = 3.62 / 3;
    features.forEach((f, i) => {
      const fy = 1.04 + i * featureH;
      s.addText(f.head, {
        x: 0.45, y: fy + 0.08, w: 5.25, h: 0.32,
        fontSize: 12, fontFace: 'Trebuchet MS', bold: true, color: DGRAY, margin: 0
      });
      s.addText(f.body, {
        x: 0.45, y: fy + 0.44, w: 5.25, h: 0.68,
        fontSize: 10.5, fontFace: 'Calibri', color: MGRAY, margin: 0, lineSpacingMultiple: 1.35
      });
      if (i < 2) hRule(pres, s, 0.45, fy + featureH - 0.04, 5.25);
    });

    hRule(pres, s, 0.45, 4.68, 5.25);
    s.addText('Included with every MDF contract — at no additional charge.', {
      x: 0.45, y: 4.76, w: 5.25, h: 0.22,
      fontSize: 9.5, fontFace: 'Calibri', italic: true, color: '2E7D52', margin: 0
    });

    vRule(pres, s, 5.90, 0.94, 3.90);

    const qcStats = [
      { label: 'TARGET INSPECTION SCORE', val: '90%+', cap: 'Tracked and reported every week' },
      { label: 'AVERAGE RESPONSE TIME',   val: '<2hr',  cap: 'From ticket open to acknowledgment' },
      { label: 'AVERAGE RESOLUTION TIME', val: '<24hr', cap: 'From issue flagged to issue closed' },
    ];

    const statH = 3.62 / 3;
    qcStats.forEach((st, i) => {
      const sy = 1.04 + i * statH;
      s.addText(st.label, {
        x: 6.10, y: sy + 0.08, w: 3.45, h: 0.20,
        fontSize: 7, fontFace: 'Calibri', bold: true, color: LGRAY, charSpacing: 2.5, margin: 0
      });
      s.addText(st.val, {
        x: 6.10, y: sy + 0.30, w: 3.45, h: 0.72,
        fontSize: 46, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
      });
      s.addText(st.cap, {
        x: 6.10, y: sy + 0.98, w: 3.45, h: 0.20,
        fontSize: 9.5, fontFace: 'Calibri', color: LGRAY, margin: 0
      });
      if (i < 2) hRule(pres, s, 6.10, sy + statH - 0.04, 3.45);
    });

    logoMDF(s);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 7 — GANTT (full width, no addTable)
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Ramp-Up Plan', 7);

    s.addText('Your Ramp-Up. Before Day One.', {
      x: 0.45, y: 0.38, w: 9, h: 0.46,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });

    const gx = 0.45, gy = 0.98, lw = 2.55, totalW = 9.1;
    const phases = ['Wk -2', 'Wk -1', 'Week 1', 'Week 2', 'Mo. 2', 'Mo. 3'];
    const pw = (totalW - lw) / 6;
    const rows = [
      { label: 'CEO + QA Manager Site Walk',    bars: [{ i: 0 }, { i: 1 }], color: 'B8760A' },
      { label: 'Key Handoff & Supply Staging',  bars: [{ i: 0 }, { i: 1 }], color: 'B8760A' },
      { label: 'Team Assignment & Orientation', bars: [{ i: 1 }],            color: 'B8760A' },
      { label: 'Service Launch',                bars: [{ i: 2 }],            color: NAVY },
      { label: 'Daily Supervisor Check-Ins',    bars: [{ i: 2 }, { i: 3 }], color: NAVY },
      { label: 'OrangeQC Baseline Report',      bars: [{ i: 2 }, { i: 3 }], color: NAVY },
      { label: '30-Day Review Call',            bars: [{ i: 4 }],            color: '2E6B3E' },
      { label: '90-Day QBR & Scope Review',     bars: [{ i: 5 }],            color: '2E6B3E' },
    ];

    const hdrH = 0.38;
    const rowH = (4.12 - hdrH) / rows.length;

    // Header row
    s.addShape('rect', {
      x: gx, y: gy, w: totalW, h: hdrH,
      fill: { color: '1A2B4A' }, line: { color: '1A2B4A' }
    });
    s.addText('ACTIVITY', {
      x: gx + 0.12, y: gy + 0.10, w: lw - 0.15, h: 0.22,
      fontSize: 7.5, fontFace: 'Calibri', bold: true, color: 'B8760A', charSpacing: 2, margin: 0
    });
    phases.forEach((ph, i) => {
      s.addText(ph, {
        x: gx + lw + i * pw, y: gy + 0.10, w: pw, h: 0.22,
        fontSize: 8, fontFace: 'Calibri', bold: true, align: 'center', color: 'AABBD4', margin: 0
      });
    });

    rows.forEach((row, ri) => {
      const ry = gy + hdrH + ri * rowH;
      const rowFill = ri % 2 === 0 ? WHITE : 'F4F7FB';

      s.addShape('rect', {
        x: gx, y: ry, w: totalW, h: rowH,
        fill: { color: rowFill }, line: { color: 'E5E7EB' }
      });
      s.addText(row.label, {
        x: gx + 0.14, y: ry + (rowH - 0.24) / 2, w: lw - 0.20, h: 0.24,
        fontSize: 9.5, fontFace: 'Calibri', color: NAVY, margin: 0
      });

      row.bars.forEach(b => {
        s.addShape('rect', {
          x: gx + lw + b.i * pw + 0.06, y: ry + rowH * 0.18,
          w: pw - 0.12, h: rowH * 0.64,
          fill: { color: row.color }, line: { color: row.color }
        });
      });
    });

    // Legend
    [
      { c: 'B8760A', l: 'Pre-Start' },
      { c: NAVY,     l: 'Active Service' },
      { c: '2E6B3E', l: 'Milestone Review' }
    ].forEach((leg, i) => {
      s.addShape('rect', {
        x: 0.45 + i * 2.6, y: 5.18, w: 0.20, h: 0.14,
        fill: { color: leg.c }, line: { color: leg.c }
      });
      s.addText(leg.l, {
        x: 0.72 + i * 2.6, y: 5.16, w: 2.3, h: 0.18,
        fontSize: 8.5, fontFace: 'Calibri', color: MGRAY, margin: 0
      });
    });

    logoMDF(s);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 8 — SOCIAL PROOF
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Client Results', 8);

    s.addText('What Our Clients Say.', {
      x: 0.45, y: 0.38, w: 7.5, h: 0.46,
      fontSize: 22, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    s.addText("Facilities that can't afford to get it wrong — and don't.", {
      x: 0.45, y: 0.86, w: 7, h: 0.26,
      fontSize: 11, fontFace: 'Calibri', color: MGRAY, margin: 0
    });
    hRule(pres, s, 0.45, 1.18, 8.08);

    // Hero quote
    s.addText(`"${HERO_QUOTE}"`, {
      x: 0.45, y: 1.28, w: 7.55, h: 1.12,
      fontSize: 13, fontFace: 'Calibri', italic: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.4
    });
    s.addText(`— ${HERO_SOURCE}`, {
      x: 0.45, y: 2.44, w: 7.55, h: 0.24,
      fontSize: 9.5, fontFace: 'Calibri', color: MGRAY, margin: 0
    });
    hRule(pres, s, 0.45, 2.74, 7.60);

    // Two secondary quotes side by side
    [[QUOTE2, SOURCE2, 0.45], [QUOTE3, SOURCE3, 4.22]].forEach(([q, src, qx]) => {
      s.addText(`"${q}"`, {
        x: qx, y: 2.84, w: 3.55, h: 1.08,
        fontSize: 10, fontFace: 'Calibri', italic: true, color: MGRAY, margin: 0, lineSpacingMultiple: 1.35
      });
      s.addText(`— ${src}`, {
        x: qx, y: 3.96, w: 3.55, h: 0.22,
        fontSize: 9, fontFace: 'Calibri', color: LGRAY, margin: 0
      });
    });
    hRule(pres, s, 0.45, 4.24, 7.60);

    // Fourth quote
    s.addText(`"${QUOTE4}"`, {
      x: 0.45, y: 4.32, w: 7.55, h: 0.50,
      fontSize: 10, fontFace: 'Calibri', italic: true, color: MGRAY, margin: 0
    });
    s.addText(`— ${SOURCE4}`, {
      x: 0.45, y: 4.86, w: 7.55, h: 0.20,
      fontSize: 9, fontFace: 'Calibri', color: LGRAY, margin: 0
    });

    // Right column — real logo images
    vRule(pres, s, 8.22, 1.18, 3.70);

    s.addImage({
      path: './logo_faa.png', x: 8.32, y: 1.30, w: 1.30, h: 1.00,
      sizing: { type: 'contain', w: 1.30, h: 1.00 }
    });
    s.addText('Certified Past Performance', {
      x: 8.32, y: 2.35, w: 1.35, h: 0.30,
      fontSize: 7, fontFace: 'Calibri', color: LGRAY, align: 'center', margin: 0
    });

    s.addImage({
      path: './logo_army.png', x: 8.32, y: 2.74, w: 1.30, h: 1.00,
      sizing: { type: 'contain', w: 1.30, h: 1.00 }
    });
    s.addText('Past Performance', {
      x: 8.32, y: 3.79, w: 1.35, h: 0.30,
      fontSize: 7, fontFace: 'Calibri', color: LGRAY, align: 'center', margin: 0
    });

    s.addImage({
      path: './logo_issa.png', x: 8.32, y: 4.16, w: 1.30, h: 0.55,
      sizing: { type: 'contain', w: 1.30, h: 0.55 }
    });
    s.addText('Industry Member', {
      x: 8.32, y: 4.75, w: 1.35, h: 0.20,
      fontSize: 7, fontFace: 'Calibri', color: LGRAY, align: 'center', margin: 0
    });
    // Note: no MDF logo on this slide — right column is already dense
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SLIDE 9 — INVESTMENT
  // ══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    slideHeader(pres, s, 'Your Investment & Next Steps', 9);

    // Left half
    s.addText('YOUR INVESTMENT', {
      x: 0.45, y: 0.38, w: 4.5, h: 0.20,
      fontSize: 7, fontFace: 'Calibri', bold: true, color: LGRAY, charSpacing: 3.5, margin: 0
    });
    s.addText(`$${MONTHLY_REVENUE.toLocaleString()}`, {
      x: 0.45, y: 0.62, w: 4.8, h: 0.92,
      fontSize: 52, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    s.addText(`per month  ·  $${ANNUAL_REVENUE.toLocaleString()} annually  ·  ${CONTRACT_TERM}`, {
      x: 0.45, y: 1.58, w: 4.8, h: 0.26,
      fontSize: 10, fontFace: 'Calibri', color: MGRAY, margin: 0
    });
    hRule(pres, s, 0.45, 1.90, 5.0);

    const lineItems = [
      { label: 'OrangeQC Inspection Reporting', val: 'Included', green: true  },
      { label: 'Dedicated QA Manager',          val: 'Included', green: true  },
      { label: 'Ownership Direct Line',         val: 'Included', green: true  },
      { label: 'W-2 Employed Staff',            val: 'Included', green: true  },
      { label: 'Supply & Equipment Management', val: 'Included', green: true  },
    ];
    const liH = 0.42;
    lineItems.forEach((li, i) => {
      const ly = 2.00 + i * liH;
      s.addShape('rect', {
        x: 0.45, y: ly, w: 5.0, h: liH,
        fill: { color: i % 2 === 0 ? WHITE : 'F9FAFB' },
        line: { color: 'F3F4F6' }
      });
      s.addText(li.label, {
        x: 0.60, y: ly + 0.08, w: 3.2, h: 0.24,
        fontSize: 10, fontFace: 'Calibri', color: li.green ? GREEN : DGRAY, margin: 0
      });
      s.addText(li.val, {
        x: 3.90, y: ly + 0.08, w: 1.35, h: 0.24,
        fontSize: 10, fontFace: 'Calibri', bold: !li.green, align: 'right',
        color: li.green ? GREEN : NAVY, margin: 0
      });
    });

    const totalY = 2.00 + lineItems.length * liH + 0.06;
    s.addShape('rect', {
      x: 0.45, y: totalY, w: 5.0, h: 0.46,
      fill: { color: NAVY }, line: { color: NAVY }
    });
    s.addText('Monthly Total', {
      x: 0.62, y: totalY + 0.12, w: 2.8, h: 0.26,
      fontSize: 11, fontFace: 'Calibri', bold: true, color: WHITE, margin: 0
    });
    s.addText(`$${MONTHLY_REVENUE.toLocaleString()}`, {
      x: 3.60, y: totalY + 0.10, w: 1.65, h: 0.30,
      fontSize: 13, fontFace: 'Trebuchet MS', bold: true, align: 'right', color: 'B8760A', margin: 0
    });

    vRule(pres, s, 5.60, 0.38, 4.95);

    // Right half
    s.addText('READY TO MOVE FORWARD?', {
      x: 5.80, y: 0.38, w: 3.75, h: 0.20,
      fontSize: 7, fontFace: 'Calibri', bold: true, color: LGRAY, charSpacing: 3.5, margin: 0
    });
    s.addText('What happens when\nyou say yes:', {
      x: 5.80, y: 0.62, w: 3.75, h: 0.78,
      fontSize: 18, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.1
    });

    const steps = [
      'Agreement signed & start date confirmed',
      'CEO + QA Manager schedule facility site walk',
      'Team assigned, keys exchanged, supplies staged',
      'Inspection dashboard created — you get login access',
      `First service delivered on your start date, July 1, 2026`,
    ];
    const stepY0 = 1.52;
    const stepH  = 3.65 / steps.length;

    steps.forEach((step, i) => {
      const sy = stepY0 + i * stepH;
      s.addText(String(i + 1), {
        x: 5.80, y: sy, w: 0.30, h: 0.32,
        fontSize: 13, fontFace: 'Trebuchet MS', bold: true, color: 'B8760A', margin: 0
      });
      s.addShape('rect', {
        x: 5.80, y: sy + 0.34, w: 0.30, h: 0.025,
        fill: { color: 'B8760A' }, line: { color: 'B8760A' }
      });
      s.addText(step, {
        x: 6.18, y: sy + 0.04, w: 3.35, h: 0.52,
        fontSize: 10.5, fontFace: 'Calibri', color: DGRAY, margin: 0, lineSpacingMultiple: 1.2
      });
    });

    hRule(pres, s, 5.80, 5.05, 3.75);
    s.addText('Hereford Johnson', {
      x: 5.80, y: 5.12, w: 3.75, h: 0.28,
      fontSize: 12, fontFace: 'Trebuchet MS', bold: true, color: NAVY, margin: 0
    });
    s.addText('623-321-2542  ·  office@maddogcleaning.com', {
      x: 5.80, y: 5.38, w: 3.75, h: 0.22,
      fontSize: 9.5, fontFace: 'Calibri', color: MGRAY, margin: 0
    });

    logoMDF(s);
  }

  await pres.writeFile({ fileName: 'MDF_Proposal_LogicalSystems_2026-05-28.pptx' });
  console.log('Saved: MDF_Proposal_LogicalSystems_2026-05-28.pptx');
}

build().catch(err => { console.error(err); process.exit(1); });
