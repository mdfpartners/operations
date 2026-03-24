#!/usr/bin/env python3
import tempfile
import os
from weasyprint import HTML

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    @page { margin: 0; }
    body {
      font-family: Arial, sans-serif;
      font-size: 10pt;
      margin: 0;
      padding: 0;
      color: #17262f;
      background: #ffffff;
    }
    .header-bar {
      background-color: #121c22;
      color: #ffffff;
      padding: 28px 40px 20px 40px;
      text-align: center;
    }
    .header-bar h1 {
      font-size: 18pt;
      margin: 0 0 4px 0;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #ffffff;
    }
    .header-bar h2 {
      font-size: 13pt;
      margin: 0 0 10px 0;
      font-weight: normal;
      color: #bc3c23;
      letter-spacing: 1px;
    }
    .header-bar .subtitle {
      font-size: 9.5pt;
      color: #abafb5;
      letter-spacing: 0.5px;
    }
    .accent-bar {
      background-color: #bc3c23;
      height: 4px;
    }
    .content {
      padding: 24px 40px 16px 40px;
    }
    h3 {
      font-size: 10pt;
      margin-top: 20px;
      margin-bottom: 6px;
      padding-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #121c22;
      border-bottom: 2px solid #bc3c23;
    }
    p { margin: 6px 0; line-height: 1.55; color: #17262f; }
    ul { margin: 6px 0 6px 20px; padding: 0; }
    li { margin-bottom: 4px; line-height: 1.55; color: #17262f; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 8.5pt; }
    th {
      background-color: #121c22;
      color: #ffffff;
      padding: 7px 8px;
      text-align: left;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 8pt;
    }
    td { border: 1px solid #d4d7d9; padding: 5px 8px; vertical-align: top; color: #17262f; }
    tr:nth-child(even) td { background-color: #f4f5f6; }
    .tools { margin-top: 8px; }
    .tool {
      display: inline-block;
      background: #121c22;
      color: #ffffff;
      border-radius: 3px;
      padding: 3px 10px;
      font-size: 8.5pt;
      margin: 3px 4px 3px 0;
      letter-spacing: 0.3px;
    }
    .escalation-box {
      background: #fff5f4;
      border-left: 4px solid #bc3c23;
      padding: 10px 14px;
      margin-top: 8px;
      font-size: 9.5pt;
      line-height: 1.55;
    }
    .footer {
      background-color: #121c22;
      color: #abafb5;
      text-align: center;
      font-size: 8.5pt;
      padding: 12px 40px;
      margin-top: 24px;
    }
    .footer span { color: #bc3c23; }
  </style>
</head>
<body>

<div class="header-bar">
  <h1>Mad Dog Facility Partners</h1>
  <h2>Operations Coordinator (PMO)</h2>
  <div class="subtitle">Part-time contractor &middot; 8&ndash;10 hrs/week &middot; Mon&ndash;Thu &middot; LATAM-based &middot; Remote &middot; $10&ndash;12/hr</div>
</div>
<div class="accent-bar"></div>

<div class="content">

<h3>About Mad Dog Facility Partners</h3>
<p>Mad Dog Facility Partners (MDF) is a service-disabled veteran-owned small business providing janitorial and security staffing services to government, industrial, and correctional facilities across the Phoenix metro area and Midwest. We are a family-owned company with over 20 years of history in Central Illinois and a culture built on reliability, accountability, and people-first leadership.</p>
<p>We are growing and need a sharp, organized coordinator to help keep our team aligned, our pipelines moving, and our operations running without things falling through the cracks.</p>

<h3>Role Overview</h3>
<p>The Operations Coordinator is the operational backbone of the MDF team. You will own our daily project tracker &mdash; logging status updates, adding new adhoc items as they arise, and keeping every active initiative current so leadership always knows exactly where things stand. You will run accountability follow-up after our morning standups, manage our candidate and subcontractor bench pipelines, support the initial phase of recruiting, and step in wherever the team needs a hand to keep things moving.</p>
<p>You do not make strategic decisions &mdash; you make sure the people who do never have to ask &ldquo;where does this stand&rdquo; on anything. This role reports directly to the CEO and works alongside our operations lead, HR coordinator, and LATAM support team.</p>

<h3>Core Responsibilities</h3>
<ul>
  <li>Attend or review the daily Teams standup (Mon&ndash;Thu) and log each team member&rsquo;s commitments into the project tracker</li>
  <li>Maintain the project tracker daily &mdash; add new adhoc items as they come up, update status notes with date stamps on all active initiatives, and flag anything that is lagging or at risk</li>
  <li>Follow up same-day or next morning on any open items at risk of slipping; escalate Red flags to the CEO via Teams message immediately &mdash; do not wait for the next standup</li>
  <li>Own the bench pipeline: conduct outreach and check-ins every 4&ndash;6 weeks with post-R1 candidates and vetted subcontractors to confirm availability and interest; keep records current</li>
  <li>Conduct cold call outreach to prospective subcontractors in target markets as directed &mdash; introduce MDF, qualify availability and service capabilities, and log qualified subs into the bench tracker by market</li>
  <li>Support the initial phase of recruiting: review incoming applications, conduct first-touch outreach to qualified candidates, and schedule first-round interviews on behalf of the HR coordinator</li>
  <li>Prepare the weekly dashboard summary for Monday and Friday standups &mdash; pull Red/Yellow flags, bench counts, and initiative statuses into a clean one-page view</li>
  <li>Log any missed or late tasks into the Accountability Log with date, owner, reason, and resolution</li>
  <li>Offer hands-on support wherever the team is lagging &mdash; step in on open tasks, follow up on outstanding items, and proactively identify where things need attention before being asked</li>
</ul>

<h3>Expected Weekly Schedule</h3>
<table>
  <tr>
    <th>Day</th>
    <th>Task</th>
    <th>Time</th>
    <th>Details</th>
  </tr>
  <tr>
    <td>Monday</td>
    <td>Standup log + tracker reset</td>
    <td>45 min</td>
    <td>Attend standup, log commitments, reset weekly checklist for new week, prepare Monday dashboard view for standup</td>
  </tr>
  <tr>
    <td>Monday</td>
    <td>Project tracker review</td>
    <td>30 min</td>
    <td>Review all active adhoc initiatives, add date-stamped status note to any row not updated in 3+ days, add new items as directed</td>
  </tr>
  <tr>
    <td>Tuesday</td>
    <td>Standup log + follow-up nudges</td>
    <td>45 min</td>
    <td>Log standup commitments, follow up on Yellow/Red items from Monday via Teams, escalate unresolved items to CEO</td>
  </tr>
  <tr>
    <td>Tuesday</td>
    <td>Bench pipeline check-ins</td>
    <td>45 min</td>
    <td>Contact candidates and subs due for 4&ndash;6 week check-in; update bench tracker with current availability and interest status</td>
  </tr>
  <tr>
    <td>Wednesday</td>
    <td>Standup log + tracker update</td>
    <td>45 min</td>
    <td>Log standup, update project tracker with new developments, add any new adhoc items surfaced by team or CEO</td>
  </tr>
  <tr>
    <td>Wednesday</td>
    <td>Subcontractor cold outreach</td>
    <td>30 min</td>
    <td>Cold call prospective subcontractors in priority markets; qualify availability and capabilities; log results and add qualified subs to bench tracker</td>
  </tr>
  <tr>
    <td>Wednesday</td>
    <td>Recruiting support</td>
    <td>30 min</td>
    <td>Review new applicants, conduct first-touch outreach to qualified candidates, schedule first-round interviews for HR coordinator</td>
  </tr>
  <tr>
    <td>Thursday</td>
    <td>Standup log + accountability review</td>
    <td>45 min</td>
    <td>Log standup, review full weekly checklist for missed items, log to Accountability Log, flag to CEO via Teams</td>
  </tr>
  <tr>
    <td>Thursday</td>
    <td>Friday standup prep + general support</td>
    <td>30 min</td>
    <td>Compile week completion rate, pull Red/Yellow flags, update dashboard for Friday standup; use remaining time to offer support on any lagging open items across the team</td>
  </tr>
</table>

<h3>What We&rsquo;re Looking For</h3>
<ul>
  <li>Exceptionally organized &mdash; you track details without being asked twice</li>
  <li>Strong written and spoken English &mdash; your Teams messages, status notes, and cold calls are clear and professional</li>
  <li>Comfortable on the phone &mdash; cold calling subcontractors requires confidence, brevity, and a professional tone</li>
  <li>Proactive communicator &mdash; you follow up without needing to be chased and surface problems before they become fires</li>
  <li>Comfortable with Excel &mdash; you can maintain a structured project tracker and keep it accurate daily</li>
  <li>Reliable and consistent &mdash; this role runs on cadence; showing up on schedule matters</li>
  <li>Experience in operations coordination, virtual assistance, recruiting support, or project support preferred</li>
  <li>Facility services, staffing, or construction industry background a plus but not required</li>
</ul>

<h3>Tools You Will Use</h3>
<div class="tools">
  <span class="tool">Microsoft Teams</span>
  <span class="tool">Excel (OneDrive)</span>
  <span class="tool">Email</span>
  <span class="tool">Phone / VOIP</span>
  <span class="tool">Indeed (recruiting)</span>
  <span class="tool">OrangeQC (read only)</span>
</div>

<h3>Escalation Protocol</h3>
<div class="escalation-box">
  When a task goes Red &mdash; missed deadline, no response after two nudges, or a blocker with no owner &mdash; send a direct Teams message to the CEO immediately with the task name, owner, and last known status. Do not wait for the next standup. Same-day escalation is expected.
</div>

</div><!-- /content -->

<div class="footer">
  Mad Dog Facility Partners &middot; <span>maddogcleaning.com</span> &middot; 309.966.0060 &middot; office@maddogcleaning.com
</div>

</body>
</html>"""

# Write to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', encoding='utf-8', delete=False) as f:
    f.write(html_content)
    tmp_path = f.name

print(f"HTML written to: {tmp_path}")

# Render PDF
output_path = '/home/user/operations/MDF_PMO_Job_Description.pdf'
HTML(filename=tmp_path).write_pdf(output_path)
print(f"PDF written to: {output_path}")

# Cleanup temp file
os.unlink(tmp_path)
print("Temp file cleaned up.")
