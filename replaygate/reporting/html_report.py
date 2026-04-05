"""Static HTML report rendering."""

from __future__ import annotations

# ruff: noqa: E501
from pathlib import Path

from jinja2 import Environment, select_autoescape

from replaygate.models import VerificationReport
from replaygate.reporting.view_models import build_report_view

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Replay Gate Report - {{ view.project_name }}</title>
  <style>
    :root {
      --bg: #f6f7f5;
      --panel: #ffffff;
      --ink: #1e2a26;
      --muted: #60716a;
      --line: #d4dcd8;
      --pass: #1f7a4d;
      --fail: #b33a24;
      --warn: #b07a13;
      --error: #8f1d1d;
      --accent: #dfe9e3;
      --shadow: 0 10px 30px rgba(34, 51, 43, 0.08);
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: linear-gradient(180deg, #edf2ee 0%, var(--bg) 28%);
      color: var(--ink);
    }
    main {
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    h1, h2, h3 { margin: 0 0 12px; line-height: 1.2; }
    h1 { font-size: 2.3rem; }
    h2 { font-size: 1.35rem; margin-top: 28px; }
    p { margin: 0 0 12px; color: var(--muted); }
    .meta-grid, .summary-grid, .issue-grid {
      display: grid;
      gap: 16px;
    }
    .meta-grid { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-top: 16px; }
    .summary-grid { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
    .issue-grid { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
    .panel, .card, .banner {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }
    .panel, .banner { padding: 22px; }
    .card { padding: 18px; }
    .eyebrow {
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 10px;
    }
    .banner { margin: 20px 0 24px; }
    .banner.pass { border-left: 8px solid var(--pass); }
    .banner.fail { border-left: 8px solid var(--fail); }
    .banner.error { border-left: 8px solid var(--error); }
    .banner.warn { border-left: 8px solid var(--warn); }
    .status-text {
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .metric {
      font-size: 1.8rem;
      font-weight: 700;
      margin-bottom: 4px;
    }
    .metric-label {
      font-size: 0.92rem;
      color: var(--muted);
    }
    .list {
      display: grid;
      gap: 10px;
      margin: 0;
      padding-left: 18px;
    }
    .breakdown-row {
      display: grid;
      grid-template-columns: 180px 1fr 44px;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
    }
    .bar {
      height: 12px;
      border-radius: 999px;
      background: #ebefec;
      overflow: hidden;
    }
    .bar > span {
      display: block;
      height: 100%;
      background: linear-gradient(90deg, #d78366, #b33a24);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 0.95rem;
    }
    th, td {
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-weight: 600;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .pill {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--accent);
      font-size: 0.82rem;
      color: var(--ink);
      margin-right: 6px;
      margin-bottom: 6px;
    }
    .filters {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 16px 0 8px;
    }
    input[type="search"], select {
      width: 100%;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #fbfcfb;
      color: var(--ink);
    }
    label.checkbox {
      display: flex;
      gap: 8px;
      align-items: center;
      padding-top: 8px;
      color: var(--muted);
    }
    details {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      background: #fafbfa;
    }
    details summary {
      cursor: pointer;
      font-weight: 600;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.85rem;
      color: #32413b;
    }
    .empty {
      color: var(--muted);
      font-style: italic;
    }
    @media (max-width: 720px) {
      .breakdown-row { grid-template-columns: 1fr; }
      table, thead, tbody, tr, th, td { display: block; }
      thead { display: none; }
      tr {
        border: 1px solid var(--line);
        border-radius: 14px;
        margin-bottom: 12px;
        padding: 10px;
        background: #fff;
      }
      td { border: 0; padding: 6px 0; }
      td::before {
        content: attr(data-label);
        display: block;
        color: var(--muted);
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
        margin-bottom: 2px;
      }
    }
  </style>
</head>
<body>
  <main>
    <header class="panel">
      <div class="eyebrow">Replay Gate Report</div>
      <h1>{{ view.project_name }}</h1>
      <p>Engine: {{ view.engine }} · Generated at {{ view.generated_at }}{% if view.git_sha %} · Git SHA {{ view.git_sha }}{% endif %}</p>
      <div class="meta-grid">
        <div class="card">
          <div class="eyebrow">Config</div>
          <div>{{ view.config_path }}</div>
        </div>
        <div class="card">
          <div class="eyebrow">Tool Version</div>
          <div>{{ view.tool_version }}</div>
        </div>
        <div class="card">
          <div class="eyebrow">Adapter Mode</div>
          <div>{{ view.adapter_mode }}</div>
        </div>
      </div>
    </header>

    <section class="banner {{ view.verdict|lower }}">
      <div class="eyebrow">Verdict</div>
      <div class="status-text">{{ view.verdict }}</div>
      <p>{{ view.policy_summary }}</p>
      <p>Policy decision: <strong>{{ view.policy_decision }}</strong> · Histories checked: <strong>{{ view.histories_checked }}</strong></p>
    </section>

    <section>
      <h2>Verification Summary</h2>
      <div class="summary-grid">
        <div class="card"><div class="metric">{{ view.histories_checked }}</div><div class="metric-label">Total histories</div></div>
        <div class="card"><div class="metric">{{ view.passed }}</div><div class="metric-label">Passed</div></div>
        <div class="card"><div class="metric">{{ view.failed }}</div><div class="metric-label">Failed</div></div>
        <div class="card"><div class="metric">{{ view.skipped }}</div><div class="metric-label">Skipped</div></div>
        <div class="card"><div class="metric">{{ view.errored }}</div><div class="metric-label">Errors</div></div>
        <div class="card"><div class="metric">{{ view.workflow_types }}</div><div class="metric-label">Workflow types covered</div></div>
      </div>
    </section>

    <section>
      <h2>Policy Decision</h2>
      <div class="panel">
        <p>{{ view.policy_summary }}</p>
        {% if view.violations %}
        <ul class="list">
          {% for violation in view.violations %}
          <li>{{ violation }}</li>
          {% endfor %}
        </ul>
        {% else %}
        <p class="empty">No policy violations.</p>
        {% endif %}
      </div>
    </section>

    <section>
      <h2>Failure Breakdown</h2>
      <div class="panel">
        {% if view.failure_breakdown %}
          {% for item in view.failure_breakdown %}
          <div class="breakdown-row">
            <strong>{{ item.label }}</strong>
            <div class="bar"><span style="width: {{ (item.count / failure_max * 100) if failure_max else 0 }}%"></span></div>
            <span>{{ item.count }}</span>
          </div>
          {% endfor %}
        {% else %}
        <p class="empty">No failures recorded.</p>
        {% endif %}
      </div>
    </section>

    <section>
      <h2>Workflow Type Breakdown</h2>
      <div class="panel">
        <table>
          <thead>
            <tr>
              <th>Workflow type</th>
              <th>Checked</th>
              <th>Passed</th>
              <th>Failed</th>
              <th>Skipped</th>
              <th>Errors</th>
              <th>Dominant failure</th>
              <th>Risk</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {% for row in view.workflow_breakdown %}
            <tr>
              <td data-label="Workflow type">{{ row.workflow_type }}</td>
              <td data-label="Checked">{{ row.checked }}</td>
              <td data-label="Passed">{{ row.passed }}</td>
              <td data-label="Failed">{{ row.failed }}</td>
              <td data-label="Skipped">{{ row.skipped }}</td>
              <td data-label="Errors">{{ row.errored }}</td>
              <td data-label="Dominant failure">{{ row.dominant_failure_kind.value if row.dominant_failure_kind else "none" }}</td>
              <td data-label="Risk">{{ row.risk_level.value }}</td>
              <td data-label="Notes">{{ row.notes or "" }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>Top Failing Histories</h2>
      {% if view.top_failures %}
      <div class="issue-grid">
        {% for result in view.top_failures %}
        <article class="card">
          <div class="eyebrow">{{ result.workflow_type }}</div>
          <h3>{{ result.path }}</h3>
          <p><span class="pill">{{ result.failure_kind }}</span><span class="pill">{{ result.risk_level }}</span></p>
          <p><strong>Summary:</strong> {{ result.summary }}</p>
          <p><strong>Likely cause:</strong> {{ result.likely_cause or "-" }}</p>
          <p><strong>Remediation hint:</strong> {{ result.remediation_hint or "-" }}</p>
          {% if result.raw_details %}
          <details>
            <summary>Raw details</summary>
            <pre>{{ result.raw_details }}</pre>
          </details>
          {% endif %}
        </article>
        {% endfor %}
      </div>
      {% else %}
      <p class="empty">No failing histories.</p>
      {% endif %}
    </section>

    <section>
      <h2>All Results</h2>
      <div class="panel">
        <div class="filters">
          <input id="searchInput" type="search" placeholder="Search history ID, file, workflow, or summary">
          <select id="workflowFilter">
            <option value="">All workflow types</option>
            {% for option in workflow_filters %}
            <option value="{{ option }}">{{ option }}</option>
            {% endfor %}
          </select>
          <select id="failureFilter">
            <option value="">All failure kinds</option>
            {% for option in failure_filters %}
            <option value="{{ option }}">{{ option }}</option>
            {% endfor %}
          </select>
          <label class="checkbox"><input id="failedOnly" type="checkbox"> Failed only</label>
        </div>
        <table id="resultsTable">
          <thead>
            <tr>
              <th>History ID</th>
              <th>File</th>
              <th>Workflow type</th>
              <th>Status</th>
              <th>Compatibility</th>
              <th>Failure kind</th>
              <th>Duration</th>
              <th>Summary</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {% for result in view.results %}
            <tr
              data-status="{{ result.status }}"
              data-workflow="{{ result.workflow_type }}"
              data-kind="{{ result.failure_kind or '' }}"
              data-search="{{ (result.history_id ~ ' ' ~ result.path ~ ' ' ~ result.workflow_type ~ ' ' ~ result.summary)|lower }}"
            >
              <td data-label="History ID">{{ result.history_id }}</td>
              <td data-label="File">{{ result.path }}</td>
              <td data-label="Workflow type">{{ result.workflow_type }}</td>
              <td data-label="Status">{{ result.status }}</td>
              <td data-label="Compatibility">{{ result.compatibility }}</td>
              <td data-label="Failure kind">{{ result.failure_kind or "none" }}</td>
              <td data-label="Duration">{{ result.duration }}</td>
              <td data-label="Summary">{{ result.summary }}</td>
              <td data-label="Details">
                <details>
                  <summary>Open</summary>
                  <p><strong>Likely cause:</strong> {{ result.likely_cause or "-" }}</p>
                  <p><strong>Remediation hint:</strong> {{ result.remediation_hint or "-" }}</p>
                  {% if result.raw_details %}
                  <pre>{{ result.raw_details }}</pre>
                  {% else %}
                  <p class="empty">No raw details.</p>
                  {% endif %}
                </details>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>Environment And Config Snapshot</h2>
      <div class="panel">
        <p><strong>Selection strategy:</strong> {{ view.selection_strategy }}</p>
        <p><strong>Max histories:</strong> {{ view.max_histories }}</p>
        <p><strong>Redact payloads in reports:</strong> {{ view.redact_payloads_in_reports }}</p>
        <p><strong>Adapter mode:</strong> {{ view.adapter_mode }}</p>
      </div>
    </section>

    <section>
      <h2>Artifacts</h2>
      <div class="panel">
        {% if view.artifacts %}
        <ul class="list">
          {% for artifact in view.artifacts %}
          <li>{{ artifact.label }}: {{ artifact.path }}</li>
          {% endfor %}
        </ul>
        {% else %}
        <p class="empty">No artifact paths recorded.</p>
        {% endif %}
      </div>
    </section>
  </main>
  <script>
    const searchInput = document.getElementById("searchInput");
    const workflowFilter = document.getElementById("workflowFilter");
    const failureFilter = document.getElementById("failureFilter");
    const failedOnly = document.getElementById("failedOnly");
    const rows = Array.from(document.querySelectorAll("#resultsTable tbody tr"));

    function applyFilters() {
      const search = searchInput.value.trim().toLowerCase();
      const workflow = workflowFilter.value;
      const failure = failureFilter.value;
      const onlyFailed = failedOnly.checked;

      rows.forEach((row) => {
        const matchesSearch = row.dataset.search.includes(search);
        const matchesWorkflow = !workflow || row.dataset.workflow === workflow;
        const matchesFailure = !failure || row.dataset.kind === failure;
        const matchesFailed = !onlyFailed || row.dataset.status === "failed" || row.dataset.status === "error";
        row.style.display = matchesSearch && matchesWorkflow && matchesFailure && matchesFailed ? "" : "none";
      });
    }

    [searchInput, workflowFilter, failureFilter, failedOnly].forEach((node) => {
      node.addEventListener("input", applyFilters);
      node.addEventListener("change", applyFilters);
    });
  </script>
</body>
</html>
"""


def render_html_report(report: VerificationReport) -> str:
    view = build_report_view(report, top_failures_limit=8)
    environment = Environment(
        autoescape=select_autoescape(enabled_extensions=("html",)),
    )
    template = environment.from_string(HTML_TEMPLATE)
    failure_max = max((item.count for item in view.failure_breakdown), default=0)
    workflow_filters = sorted({item.workflow_type for item in view.results})
    failure_filters = sorted(
        {item.failure_kind for item in view.results if item.failure_kind is not None}
    )
    return template.render(
        view=view,
        failure_max=failure_max,
        workflow_filters=workflow_filters,
        failure_filters=failure_filters,
    )


def write_html_report(report: VerificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html_report(report), encoding="utf-8")
    return output_path
