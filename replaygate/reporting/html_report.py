"""Static HTML report rendering."""

from __future__ import annotations

# ruff: noqa: E501
from pathlib import Path

from jinja2 import Environment, select_autoescape

from replaygate.models import VerificationReport, WorkflowTypeBreakdown
from replaygate.reporting.view_models import build_report_view, risk_rank

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Replay Gate Report - {{ view.project_name }}</title>
  <style>
    :root {
      --paper: #f5efdf;
      --paper-deep: #eadfca;
      --paper-line: rgba(45, 54, 69, 0.08);
      --panel: #fffdf7;
      --ink: #1f2530;
      --ink-soft: #475160;
      --muted: #5c6370;
      --line: #d8ccb5;
      --line-strong: #b9aa8d;
      --shadow: 0 14px 34px rgba(42, 35, 25, 0.08);
      --shadow-soft: 0 8px 18px rgba(42, 35, 25, 0.05);
      --navy: #16263b;
      --navy-soft: #253753;
      --pass: #2e7b68;
      --pass-soft: #d7eee7;
      --fail: #b64b2c;
      --fail-soft: #f7dfd5;
      --warn: #9d6b1b;
      --warn-soft: #f3e6c8;
      --error: #8a2c36;
      --error-soft: #f2d8dd;
      --neutral-soft: #e6e0d2;
      --heading: "Georgia", "Iowan Old Style", serif;
      --body: "Trebuchet MS", "Segoe UI", sans-serif;
      --mono: "Consolas", "SFMono-Regular", "Liberation Mono", monospace;
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      color: var(--ink);
      font-family: var(--body);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.45), rgba(255,255,255,0) 12%),
        repeating-linear-gradient(
          0deg,
          transparent 0,
          transparent 34px,
          rgba(45,54,69,0.03) 34px,
          rgba(45,54,69,0.03) 35px
        ),
        linear-gradient(180deg, #faf6ea 0%, var(--paper) 100%);
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(90deg, transparent 0, transparent calc(100% - 1px), rgba(45,54,69,0.05) calc(100% - 1px)),
        linear-gradient(90deg, rgba(22,38,59,0.035) 0, rgba(22,38,59,0.035) 1px, transparent 1px, transparent 72px);
      mask-image: linear-gradient(180deg, rgba(0,0,0,0.32), transparent 65%);
    }

    main {
      max-width: 1360px;
      margin: 0 auto;
      padding: 28px 20px 72px;
    }

    .page-grid {
      display: grid;
      grid-template-columns: 230px minmax(0, 1fr);
      gap: 20px;
      align-items: start;
    }

    .content { min-width: 0; }

    .panel,
    .rail-card,
    .card,
    .artifact-card {
      background: var(--panel);
      border: 2px solid var(--line);
      border-radius: 0;
      box-shadow: var(--shadow);
    }

    .panel,
    .rail-card,
    .artifact-card { padding: 22px; }

    .card {
      padding: 18px;
      box-shadow: var(--shadow-soft);
    }

    .page-grid > aside .rail-card {
      background: linear-gradient(180deg, #1d2d43 0%, #132234 100%);
      color: #f3f1e9;
      border-color: #0c1827;
    }

    .page-grid > aside .rail-card p,
    .page-grid > aside .rail-card .eyebrow {
      color: rgba(232, 237, 243, 0.76);
    }

    .rail {
      position: sticky;
      top: 24px;
      display: grid;
      gap: 12px;
    }

    .eyebrow {
      margin-bottom: 10px;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    h1, h2, h3 {
      margin: 0;
      font-family: var(--heading);
      line-height: 1.08;
      letter-spacing: -0.02em;
    }

    h1 { font-size: clamp(2.9rem, 5.1vw, 4.8rem); }
    h2 { font-size: 1.85rem; }
    h3 { font-size: 1.3rem; }

    p {
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
    }

    section[id] { scroll-margin-top: 24px; }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.85fr);
      gap: 18px;
      margin-bottom: 18px;
    }

    .hero-copy {
      margin-top: 16px;
      max-width: 54ch;
      font-size: 1.02rem;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 18px;
    }

    .chip,
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      border: 1px solid rgba(22, 38, 59, 0.12);
      font-size: 0.78rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .chip {
      background: rgba(255, 255, 255, 0.74);
      color: var(--navy-soft);
      font-family: var(--mono);
    }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 20px;
    }

    .meta-card {
      padding: 14px;
      border: 1px solid rgba(22, 38, 59, 0.12);
      background: rgba(255, 255, 255, 0.76);
      box-shadow: var(--shadow-soft);
    }

    .meta-value {
      margin-top: 8px;
      font-weight: 700;
      color: var(--ink);
      word-break: break-word;
    }

    .verdict-card {
      position: relative;
      overflow: hidden;
      display: grid;
      gap: 18px;
      background: linear-gradient(180deg, #1d2d43 0%, #111f31 100%);
      color: #f3f1e9;
      border-color: #0c1827;
    }

    .verdict-card::after {
      content: "";
      position: absolute;
      right: 22px;
      top: 22px;
      width: 116px;
      height: 116px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
    }

    .verdict-header {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }

    .verdict-card p,
    .verdict-card .eyebrow,
    .verdict-card .hero-stat-label {
      color: rgba(232, 237, 243, 0.76);
    }

    .status-text {
      margin-bottom: 12px;
      font-size: clamp(2.3rem, 4.5vw, 3.8rem);
      font-weight: 800;
      letter-spacing: -0.04em;
      line-height: 0.95;
    }

    .hero-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 20px;
    }

    .hero-stat,
    .rail-stat,
    .spotlight,
    .snapshot-item {
      padding: 14px;
      border: 1px solid rgba(22, 38, 59, 0.12);
      background: rgba(255,255,255,0.78);
      box-shadow: var(--shadow-soft);
    }

    .hero-stat,
    .rail-stat {
      background: rgba(255,255,255,0.08);
      border-color: rgba(255,255,255,0.12);
    }

    .hero-stat-value,
    .spotlight-value {
      color: var(--ink);
      font-size: 1.45rem;
      font-weight: 800;
      line-height: 1.1;
      word-break: break-word;
    }

    .hero-stat-value,
    .rail-stat strong {
      color: #fff9f1;
    }

    .hero-stat-label,
    .snapshot-label {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.7rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      font-weight: 700;
    }

    .section {
      margin-top: 18px;
      border-top: 3px solid var(--navy);
      padding-top: 14px;
    }

    .section-heading { margin-bottom: 14px; }

    .section-heading p {
      margin-top: 6px;
      max-width: 68ch;
      font-size: 0.97rem;
    }

    .summary-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(6, minmax(0, 1fr));
    }

    .summary-card {
      position: relative;
      overflow: hidden;
      border-top-width: 5px;
    }

    .summary-card::before {
      display: none;
    }

    .summary-card.neutral { color: var(--navy-soft); }
    .summary-card.pass { color: var(--pass); background: #fffdf7; }
    .summary-card.fail { color: var(--fail); background: #fffdf7; }
    .summary-card.warn { color: var(--warn); background: #fffdf7; }
    .summary-card.error { color: var(--error); background: #fffdf7; }

    .summary-card.neutral { border-top-color: var(--navy-soft); }
    .summary-card.pass { border-top-color: var(--pass); }
    .summary-card.fail { border-top-color: var(--fail); }
    .summary-card.warn { border-top-color: var(--warn); }
    .summary-card.error { border-top-color: var(--error); }

    .metric {
      margin-bottom: 8px;
      font-size: 2rem;
      font-weight: 800;
      line-height: 1;
      color: var(--ink);
    }

    .metric-label {
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .spotlight-grid,
    .issue-grid,
    .artifact-grid,
    .snapshot-grid {
      display: grid;
      gap: 12px;
    }

    .spotlight-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-bottom: 12px;
    }

    .issue-grid {
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }

    .artifact-grid,
    .snapshot-grid {
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    }

    .rule-list,
    .nav-list,
    .breakdown-list {
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .rule-list li,
    .breakdown-row {
      padding: 12px 14px;
      border-left: 4px solid var(--navy-soft);
      background: rgba(255,255,255,0.72);
      box-shadow: var(--shadow-soft);
    }

    .breakdown-row {
      display: grid;
      grid-template-columns: 180px minmax(0, 1fr) auto;
      gap: 14px;
      align-items: center;
      border: 1px solid rgba(22,38,59,0.12);
      border-left: 4px solid var(--navy-soft);
    }

    .bar {
      height: 14px;
      background: rgba(22,38,59,0.08);
      overflow: hidden;
    }

    .bar > span {
      display: block;
      height: 100%;
      background: linear-gradient(90deg, #cd7d61 0%, var(--fail) 100%);
    }

    .count {
      min-width: 66px;
      text-align: right;
      font-family: var(--mono);
      font-weight: 700;
      color: var(--ink);
    }

    .table-card { overflow: hidden; }

    .table-wrap {
      overflow-x: auto;
      margin-top: 8px;
      border: 2px solid var(--border);
      background: #fffdf7;
    }

    table {
      width: 100%;
      min-width: 860px;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 0.94rem;
    }

    th, td {
      padding: 14px 12px;
      text-align: left;
      vertical-align: top;
      border-bottom: 1px solid rgba(22,38,59,0.1);
    }

    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #ece3cf;
      color: var(--navy);
      font-family: var(--mono);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    tbody tr:nth-child(even) td { background: rgba(255,255,255,0.45); }
    tbody tr:hover td { background: rgba(255,255,255,0.72); }

    .badge {
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.03em;
    }

    .badge-pass,
    .badge-status-passed,
    .badge-compatibility-compatible,
    .badge-risk-low {
      background: var(--pass-soft);
      color: var(--pass);
      border-color: rgba(46,123,104,0.18);
    }

    .badge-fail,
    .badge-status-failed,
    .badge-compatibility-incompatible,
    .badge-kind-nondeterminism,
    .badge-risk-critical {
      background: var(--fail-soft);
      color: var(--fail);
      border-color: rgba(182,75,44,0.18);
    }

    .badge-error,
    .badge-status-error,
    .badge-kind-adapter_error,
    .badge-kind-environment_error {
      background: var(--error-soft);
      color: var(--error);
      border-color: rgba(138,44,54,0.18);
    }

    .badge-warn,
    .badge-status-skipped,
    .badge-compatibility-unknown,
    .badge-kind-unknown_workflow_type,
    .badge-kind-corrupted_history,
    .badge-kind-payload_decode_error,
    .badge-kind-policy_failure,
    .badge-risk-medium,
    .badge-risk-high {
      background: var(--warn-soft);
      color: var(--warn);
      border-color: rgba(157,107,27,0.2);
    }

    .badge-neutral {
      background: var(--neutral-soft);
      color: var(--ink);
      border-color: rgba(31,37,48,0.1);
    }

    .issue-card {
      background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(252,248,240,0.95));
      display: grid;
      gap: 14px;
      border-left: 8px solid var(--fail);
    }

    .issue-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }

    .info-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }

    .info-box {
      padding: 12px 14px;
      border: 1px solid rgba(22,38,59,0.12);
      background: rgba(255,255,255,0.72);
      box-shadow: var(--shadow-soft);
    }

    .info-label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.71rem;
      letter-spacing: 0.11em;
      text-transform: uppercase;
      font-weight: 700;
    }

    .info-value,
    .snapshot-value {
      color: var(--ink);
      font-weight: 700;
      line-height: 1.4;
      word-break: break-word;
    }

    details {
      border: 1px solid rgba(22,38,59,0.12);
      padding: 10px 12px;
      background: rgba(255,255,255,0.7);
    }

    details[open] { background: rgba(255,255,255,0.85); }

    details summary {
      cursor: pointer;
      color: var(--navy);
      font-family: var(--mono);
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    pre {
      margin: 12px 0 0;
      padding: 14px;
      border: 1px solid rgba(22,38,59,0.12);
      background: #f8f3e6;
      color: var(--ink);
      font-family: var(--mono);
      font-size: 0.84rem;
      white-space: pre-wrap;
      word-break: break-word;
      overflow: auto;
    }

    .filters {
      display: grid;
      grid-template-columns: minmax(260px, 2fr) repeat(2, minmax(170px, 1fr)) auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }

    input[type="search"],
    select {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid rgba(22,38,59,0.16);
      background: rgba(255,255,255,0.82);
      color: var(--ink);
    }

    label.checkbox {
      display: inline-flex;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .results-meta {
      margin-bottom: 12px;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .rail-status {
      display: inline-flex;
      align-items: center;
      padding: 8px 14px;
      margin-bottom: 12px;
      border: 1px solid rgba(255,255,255,0.12);
      font-weight: 800;
      font-family: var(--mono);
      letter-spacing: 0.03em;
    }

    .rail-status.passed { background: var(--pass-soft); color: var(--pass); }
    .rail-status.failed { background: var(--fail-soft); color: var(--fail); }
    .rail-status.error { background: var(--error-soft); color: var(--error); }
    .rail-status.warn { background: var(--warn-soft); color: var(--warn); }

    .rail-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }

    .rail-stat strong {
      display: block;
      font-size: 1.2rem;
      margin-bottom: 4px;
      color: #fff9f1;
    }

    .rail-stat span {
      color: rgba(232, 237, 243, 0.76);
      font-family: var(--mono);
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }

    .nav-list a {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      border: 1px solid rgba(22,38,59,0.12);
      background: rgba(255,255,255,0.72);
      box-shadow: var(--shadow-soft);
      text-decoration: none;
      color: var(--navy-soft);
      font-family: var(--mono);
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .page-grid > aside .nav-list a {
      background: rgba(255,255,255,0.08);
      border-color: rgba(255,255,255,0.12);
      color: #f3f1e9;
      box-shadow: none;
    }

    .nav-list a::after {
      content: "↗";
      color: var(--muted);
      font-size: 0.84rem;
    }

    .page-grid > aside .nav-list a::after {
      color: rgba(232, 237, 243, 0.58);
    }

    .artifact-path {
      margin-top: 8px;
      color: var(--ink);
      font-family: var(--mono);
      font-size: 0.84rem;
      font-weight: 700;
      line-height: 1.45;
      word-break: break-word;
    }

    .page-grid > aside .artifact-path {
      color: #f3f1e9;
    }

    .empty,
    .empty-state {
      color: var(--muted);
      font-style: italic;
    }

    .empty-state {
      margin-bottom: 12px;
      padding: 14px 16px;
      border: 1px dashed rgba(22,38,59,0.2);
      background: rgba(255,255,255,0.6);
    }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 6;
      display: grid;
      grid-template-columns: minmax(220px, 1.2fr) minmax(0, 2fr);
      gap: 12px;
      align-items: center;
      margin-bottom: 18px;
      padding: 12px 16px;
      border-bottom: 3px solid #0b1421;
      background: rgba(19, 29, 43, 0.96);
      color: #f3f1e9;
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.18);
      backdrop-filter: blur(10px);
    }

    .topbar-title {
      display: grid;
      gap: 4px;
    }

    .topbar-brand {
      font-family: var(--mono);
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(233, 238, 244, 0.72);
    }

    .topbar-project {
      font-size: 1rem;
      font-weight: 700;
      color: #fff9f1;
    }

    .topbar-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }

    .topbar-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      border: 1px solid rgba(255,255,255,0.14);
      background: rgba(255,255,255,0.08);
      color: #f3f1e9;
      font-family: var(--mono);
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .topbar-pill strong {
      font-size: 0.95rem;
      color: #fff9f1;
    }

    .topbar-pill.failed strong,
    .topbar-pill.failed { color: #ffd5cc; }
    .topbar-pill.passed strong,
    .topbar-pill.passed { color: #d7eee7; }
    .topbar-pill.error strong,
    .topbar-pill.error { color: #f2d8dd; }

    .report-shell {
      display: grid;
      gap: 18px;
    }

    .report-head {
      display: grid;
      gap: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line-strong);
    }

    .report-kicker {
      color: var(--navy-soft);
      font-family: var(--mono);
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .report-head h1 {
      margin-top: 6px;
      font-size: 2rem;
      max-width: none;
    }

    .report-meta {
      margin-top: 6px;
      color: var(--ink-soft);
      font-size: 0.95rem;
    }

    .report-utility {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }

    .utility-item {
      padding: 12px 14px;
      border-left: 3px solid var(--navy-soft);
      background: rgba(255,255,255,0.62);
    }

    .subnav {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid rgba(22,38,59,0.12);
    }

    .subnav a {
      padding: 8px 10px;
      background: rgba(255,255,255,0.7);
      border: 1px solid rgba(22,38,59,0.12);
      color: var(--navy-soft);
      font-family: var(--mono);
      font-size: 0.76rem;
      font-weight: 700;
      text-decoration: none;
      text-transform: uppercase;
    }

    .section-block {
      display: grid;
      gap: 12px;
    }

    .section-block .section-heading {
      margin-bottom: 0;
    }

    .two-up {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .plain-panel {
      padding: 18px;
      border: 1px solid rgba(22,38,59,0.12);
      background: rgba(255,255,255,0.72);
      box-shadow: var(--shadow-soft);
    }

    .plain-panel h3 {
      margin-bottom: 8px;
      font-size: 1.15rem;
    }

    .plain-list {
      display: grid;
      gap: 10px;
      margin: 14px 0 0;
      padding: 0;
      list-style: none;
    }

    .plain-list li {
      padding: 10px 12px;
      border-left: 3px solid var(--fail);
      background: rgba(255,255,255,0.68);
      color: var(--ink);
    }

    .diagnosis-grid {
      display: grid;
      gap: 12px;
      margin-top: 12px;
    }

    .diagnosis-item {
      display: grid;
      gap: 5px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(22,38,59,0.1);
    }

    .diagnosis-item:last-child {
      padding-bottom: 0;
      border-bottom: 0;
    }

    .diagnosis-item strong {
      color: var(--ink);
    }

    .report-shell table {
      min-width: 0;
      table-layout: fixed;
    }

    .report-shell td,
    .report-shell th {
      word-break: break-word;
    }

    .compact-table th:nth-child(1),
    .compact-table td:nth-child(1) { width: 16%; }
    .compact-table th:nth-child(2),
    .compact-table td:nth-child(2) { width: 10%; }
    .compact-table th:nth-child(3),
    .compact-table td:nth-child(3) { width: 10%; }
    .compact-table th:nth-child(4),
    .compact-table td:nth-child(4) { width: 18%; }
    .compact-table th:nth-child(5),
    .compact-table td:nth-child(5) { width: 12%; }

    .results-table th:nth-child(1),
    .results-table td:nth-child(1) { width: 10%; }
    .results-table th:nth-child(2),
    .results-table td:nth-child(2) { width: 14%; }
    .results-table th:nth-child(3),
    .results-table td:nth-child(3) { width: 16%; }
    .results-table th:nth-child(4),
    .results-table td:nth-child(4) { width: 14%; }
    .results-table th:nth-child(5),
    .results-table td:nth-child(5) { width: 24%; }
    .results-table th:nth-child(6),
    .results-table td:nth-child(6) { width: 10%; }
    .results-table th:nth-child(7),
    .results-table td:nth-child(7) { width: 12%; }

    .advanced-panel {
      border: 2px solid var(--line);
      background: rgba(255,255,255,0.72);
      box-shadow: var(--shadow);
    }

    .advanced-panel summary {
      padding: 16px 18px;
      cursor: pointer;
      color: var(--navy);
      font-family: var(--mono);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .advanced-panel[open] summary {
      border-bottom: 1px solid rgba(22,38,59,0.12);
    }

    .advanced-body {
      display: grid;
      gap: 12px;
      padding: 18px;
    }

    @media (max-width: 1120px) {
      .topbar {
        grid-template-columns: 1fr;
      }
      .topbar-strip {
        justify-content: flex-start;
      }
      .page-grid { grid-template-columns: 1fr; }
      .rail { display: none; }
      .hero { grid-template-columns: 1fr; }
      .summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .two-up,
      .spotlight-grid { grid-template-columns: 1fr; }
    }

    @media (max-width: 760px) {
      main { padding-inline: 14px; }
      .topbar-pill {
        width: 100%;
        justify-content: space-between;
      }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .filters { grid-template-columns: 1fr; }
      .subnav { display: grid; }
      .breakdown-row { grid-template-columns: 1fr; }
      .hero-stats,
      .rail-stats { grid-template-columns: 1fr 1fr; }
      .report-head h1 {
        font-size: 1.6rem;
      }

      table,
      thead,
      tbody,
      tr,
      th,
      td { display: block; }

      table { min-width: 0; }
      thead { display: none; }
      .table-wrap { overflow: visible; background: transparent; }

      tr {
        margin-bottom: 12px;
        border: 1px solid rgba(22,38,59,0.14);
        background: rgba(255,255,255,0.8);
        box-shadow: var(--shadow-soft);
        overflow: hidden;
      }

      td {
        padding: 10px 14px;
        border: 0;
      }

      td::before {
        content: attr(data-label);
        display: block;
        margin-bottom: 4px;
        color: var(--muted);
        font-family: var(--mono);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      tbody tr:nth-child(even) td,
      tbody tr:hover td { background: transparent; }
    }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-title">
      <span class="topbar-brand">Replay Gate</span>
      <span class="topbar-project">{{ view.project_name }}</span>
    </div>
    <div class="topbar-strip">
      <span class="topbar-pill {{ view.verdict|lower }}"><strong>{{ view.verdict }}</strong></span>
      <span class="topbar-pill"><strong>{{ view.histories_checked }}</strong> checked</span>
      <span class="topbar-pill"><strong>{{ view.failed }}</strong> failed</span>
      <span class="topbar-pill"><strong>{{ dominant_failure.label if dominant_failure else "none" }}</strong> dominant failure</span>
      <span class="topbar-pill"><strong>{{ view.policy_decision }}</strong> policy</span>
    </div>
  </div>

  <main class="report-shell">
    <header class="report-head">
      <div>
        <div class="report-kicker">Replay verification report</div>
        <h1>{{ view.project_name }}</h1>
        <p class="report-meta">Project {{ view.project_name }} · Engine {{ view.engine }} · Generated {{ view.generated_at }}{% if view.git_sha %} · Git SHA {{ view.git_sha }}{% endif %}</p>
      </div>
      <div class="report-utility">
        <div class="utility-item"><div class="eyebrow">Config</div><div class="meta-value">{{ view.config_path }}</div></div>
        <div class="utility-item"><div class="eyebrow">Selection strategy</div><div class="meta-value">{{ view.selection_strategy }}</div></div>
        <div class="utility-item"><div class="eyebrow">Adapter mode</div><div class="meta-value">{{ view.adapter_mode }}</div></div>
        <div class="utility-item"><div class="eyebrow">Tool version</div><div class="meta-value">{{ view.tool_version }}</div></div>
      </div>
    </header>

    <nav class="subnav" aria-label="Report sections">
      {% for link in section_links %}
      <a href="#{{ link.id }}">{{ link.label }}</a>
      {% endfor %}
    </nav>

    <section id="why-this-failed" class="section section-block">
      <div class="section-heading">
        <h2>{{ diagnosis_heading }}</h2>
        <p>The first screen is optimized for the deployment decision: what failed, what is affected, and what to do next.</p>
      </div>
      <div class="two-up">
        <article class="plain-panel">
          <div class="eyebrow">Policy decision</div>
          <h3>{{ view.policy_decision|upper }}</h3>
          <p>{{ view.policy_summary }}</p>
          {% if view.violations %}
          <ul class="plain-list">
            {% for violation in view.violations %}
            <li>{{ violation }}</li>
            {% endfor %}
          </ul>
          {% else %}
          <p class="empty" style="margin-top: 12px;">No policy violations.</p>
          {% endif %}
        </article>
        <article class="plain-panel">
          <div class="eyebrow">Diagnosis</div>
          <div class="diagnosis-grid">
            <div class="diagnosis-item">
              <span class="eyebrow">Most affected workflow</span>
              <strong>{{ highlight_workflow.workflow_type if highlight_workflow else "none" }}</strong>
              <p>{% if highlight_workflow %}Risk {{ highlight_workflow.risk_level.value }} · {{ highlight_workflow.failed }} failed of {{ highlight_workflow.checked }} checked{% else %}No workflow breakdown available.{% endif %}</p>
            </div>
            <div class="diagnosis-item">
              <span class="eyebrow">Primary cause</span>
              <strong>{{ dominant_failure.label if dominant_failure else "none" }}</strong>
              <p>{{ top_likely_cause }}</p>
            </div>
            <div class="diagnosis-item">
              <span class="eyebrow">Recommended next action</span>
              <strong>{{ top_remediation }}</strong>
            </div>
          </div>
        </article>
      </div>
      <article class="plain-panel">
        <div class="section-heading" style="margin-bottom: 12px;">
          <h3>Failure breakdown</h3>
          <p>Failure kinds are normalized before rendering so the categories stay consistent across every surface.</p>
        </div>
        {% if view.failure_breakdown %}
        <div class="breakdown-list">
          {% for item in view.failure_breakdown %}
          <div class="breakdown-row">
            <strong>{{ item.label }}</strong>
            <div class="bar"><span style="width: {{ (item.count / failure_max * 100) if failure_max else 0 }}%"></span></div>
            <div class="count">{{ item.count }} · {{ ((item.count / view.histories_checked) * 100) | round(0) | int }}%</div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <p class="empty">No failures recorded.</p>
        {% endif %}
      </article>
    </section>

    <section id="verification-summary" class="section">
      <div class="section-heading">
        <h2>Verification Summary</h2>
        <p>Counts stay aligned with the CLI, GitHub markdown summary, and machine-readable JSON report.</p>
      </div>
      <div class="summary-grid">
        <article class="card summary-card neutral"><div class="metric">{{ view.histories_checked }}</div><div class="metric-label">Total histories</div></article>
        <article class="card summary-card pass"><div class="metric">{{ view.passed }}</div><div class="metric-label">Passed</div></article>
        <article class="card summary-card fail"><div class="metric">{{ view.failed }}</div><div class="metric-label">Failed</div></article>
        <article class="card summary-card warn"><div class="metric">{{ view.skipped }}</div><div class="metric-label">Skipped</div></article>
        <article class="card summary-card error"><div class="metric">{{ view.errored }}</div><div class="metric-label">Errors</div></article>
        <article class="card summary-card neutral"><div class="metric">{{ view.workflow_types }}</div><div class="metric-label">Workflow types covered</div></article>
      </div>
    </section>

    <section id="workflow-type-breakdown" class="section">
      <div class="section-heading">
        <h2>Affected Workflow Types</h2>
        <p>Use this table to see whether replay risk is isolated to one workflow or spread across the candidate module.</p>
      </div>
      <div class="panel table-card">
        <div class="table-wrap">
          <table class="compact-table">
            <thead>
              <tr>
                <th>Workflow</th>
                <th>Checked</th>
                <th>Failed</th>
                <th>Dominant failure</th>
                <th>Risk</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {% for row in workflow_rows %}
              <tr>
                <td data-label="Workflow"><strong>{{ row.workflow_type }}</strong></td>
                <td data-label="Checked">{{ row.checked }}</td>
                <td data-label="Failed">{{ row.failed }}</td>
                <td data-label="Dominant failure"><span class="badge {{ 'badge-kind-' ~ row.dominant_failure_kind.value if row.dominant_failure_kind else 'badge-neutral' }}">{{ row.dominant_failure_kind.value if row.dominant_failure_kind else "none" }}</span></td>
                <td data-label="Risk"><span class="badge badge-risk-{{ row.risk_level.value }}">{{ row.risk_level.value }}</span></td>
                <td data-label="Note">{{ row.notes or "" }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section id="top-failing-histories" class="section">
      <div class="section-heading">
        <h2>Top Failing Histories</h2>
        <p>These are the clearest examples of what blocked replay safety for this run.</p>
      </div>
      {% if view.top_failures %}
      <div class="issue-grid">
        {% for result in view.top_failures %}
        <article class="card issue-card">
          <div class="issue-head">
            <div>
              <div class="eyebrow">{{ result.workflow_type }}</div>
              <h3>{{ result.history_id }}</h3>
            </div>
            <div class="chip-row" style="margin-top: 0;">
              <span class="badge badge-kind-{{ result.failure_kind }}">{{ result.failure_kind }}</span>
            </div>
          </div>
          <p><strong>History:</strong> {{ result.path }}</p>
          <p><strong>Summary:</strong> {{ result.summary }}</p>
          <p><strong>Likely cause:</strong> {{ result.likely_cause or "-" }}</p>
          <p><strong>Suggested fix:</strong> {{ result.remediation_hint or "-" }}</p>
          {% if result.raw_details %}
          <details>
            <summary>Show raw details</summary>
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

    <section id="all-results" class="section">
      <div class="section-heading">
        <h2>All Results</h2>
        <p>The results table is the primary evidence surface. Secondary detail stays inside the row expansion instead of taking table width.</p>
      </div>
      <div class="panel table-card">
            <div class="filters">
              <input id="searchInput" type="search" placeholder="Search history ID, file, workflow, summary, or hint">
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
            <div class="results-meta" aria-live="polite"><span id="visibleCount">{{ view.results|length }}</span> of {{ view.results|length }} visible</div>
            <div id="resultsEmpty" class="empty-state" hidden>No results match the current filters.</div>
            <div class="table-wrap">
              <table id="resultsTable" class="results-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Workflow</th>
                    <th>History</th>
                    <th>Failure kind</th>
                    <th>Summary</th>
                    <th>Duration</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {% for result in view.results %}
                  <tr
                    data-status="{{ result.status }}"
                    data-workflow="{{ result.workflow_type }}"
                    data-kind="{{ result.failure_kind or '' }}"
                    data-search="{{ (result.history_id ~ ' ' ~ result.path ~ ' ' ~ result.workflow_type ~ ' ' ~ result.summary ~ ' ' ~ (result.likely_cause or '') ~ ' ' ~ (result.remediation_hint or ''))|lower }}"
                  >
                    <td data-label="Status"><span class="badge badge-status-{{ result.status }}">{{ result.status }}</span></td>
                    <td data-label="Workflow"><strong>{{ result.workflow_type }}</strong></td>
                    <td data-label="History">{{ result.history_id }}</td>
                    <td data-label="Failure kind"><span class="badge {{ 'badge-kind-' ~ result.failure_kind if result.failure_kind else 'badge-neutral' }}">{{ result.failure_kind or "none" }}</span></td>
                    <td data-label="Summary">{{ result.summary }}</td>
                    <td data-label="Duration">{{ result.duration }}</td>
                    <td data-label="Details">
                      <details>
                        <summary>Inspect</summary>
                        <p><strong>File:</strong> {{ result.path }}</p>
                        <p style="margin-top: 10px;"><strong>Compatibility:</strong> {{ result.compatibility }}</p>
                        <p><strong>Likely cause:</strong> {{ result.likely_cause or "-" }}</p>
                        <p style="margin-top: 10px;"><strong>Remediation hint:</strong> {{ result.remediation_hint or "-" }}</p>
                        {% if result.raw_details %}
                        <pre>{{ result.raw_details }}</pre>
                        {% else %}
                        <p class="empty" style="margin-top: 10px;">No raw details.</p>
                        {% endif %}
                      </details>
                    </td>
                  </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          </div>
    </section>

    <details id="advanced-details" class="advanced-panel section">
      <summary>Advanced details</summary>
      <div class="advanced-body">
        <section>
          <div class="section-heading">
            <h2>Environment And Config Snapshot</h2>
            <p>This is the run configuration context used to produce the current replay decision.</p>
          </div>
          <div class="snapshot-grid">
            <div class="snapshot-item"><span class="snapshot-label">Selection strategy</span><span class="snapshot-value">{{ view.selection_strategy }}</span></div>
            <div class="snapshot-item"><span class="snapshot-label">Max histories</span><span class="snapshot-value">{{ view.max_histories }}</span></div>
            <div class="snapshot-item"><span class="snapshot-label">Redact payloads in reports</span><span class="snapshot-value">{{ view.redact_payloads_in_reports }}</span></div>
            <div class="snapshot-item"><span class="snapshot-label">Adapter mode</span><span class="snapshot-value">{{ view.adapter_mode }}</span></div>
          </div>
        </section>

        <section>
          <div class="section-heading">
            <h2>Artifacts</h2>
            <p>These are the deterministic outputs Replay Gate recorded for this verification run.</p>
          </div>
          <div class="artifact-grid">
            {% if view.artifacts %}
              {% for artifact in view.artifacts %}
              <article class="artifact-card">
                <div class="eyebrow">{{ artifact.label }}</div>
                <div class="artifact-path">{{ artifact.path }}</div>
              </article>
              {% endfor %}
            {% else %}
            <div class="plain-panel"><p class="empty">No artifact paths recorded.</p></div>
            {% endif %}
          </div>
        </section>
      </div>
    </details>
  </main>
  <script>
    const searchInput = document.getElementById("searchInput");
    const workflowFilter = document.getElementById("workflowFilter");
    const failureFilter = document.getElementById("failureFilter");
    const failedOnly = document.getElementById("failedOnly");
    const rows = Array.from(document.querySelectorAll("#resultsTable tbody tr"));
    const visibleCount = document.getElementById("visibleCount");
    const resultsEmpty = document.getElementById("resultsEmpty");

    function applyFilters() {
      const search = searchInput.value.trim().toLowerCase();
      const workflow = workflowFilter.value;
      const failure = failureFilter.value;
      const onlyFailed = failedOnly.checked;
      let visible = 0;

      rows.forEach((row) => {
        const matchesSearch = row.dataset.search.includes(search);
        const matchesWorkflow = !workflow || row.dataset.workflow === workflow;
        const matchesFailure = !failure || row.dataset.kind === failure;
        const matchesFailed = !onlyFailed || row.dataset.status === "failed" || row.dataset.status === "error";
        const isVisible = matchesSearch && matchesWorkflow && matchesFailure && matchesFailed;
        row.hidden = !isVisible;
        if (isVisible) {
          visible += 1;
        }
      });

      visibleCount.textContent = String(visible);
      resultsEmpty.hidden = visible !== 0;
    }

    [searchInput, workflowFilter, failureFilter, failedOnly].forEach((node) => {
      node.addEventListener("input", applyFilters);
      node.addEventListener("change", applyFilters);
    });

    applyFilters();
  </script>
</body>
</html>
"""


def _workflow_sort_key(row: WorkflowTypeBreakdown) -> tuple[int, int, int, str]:
    return (
        -risk_rank(row.risk_level.value),
        -row.failed,
        -row.errored,
        row.workflow_type,
    )


def render_html_report(report: VerificationReport) -> str:
    view = build_report_view(report, top_failures_limit=8)
    environment = Environment(
        autoescape=select_autoescape(enabled_extensions=("html",)),
    )
    template = environment.from_string(HTML_TEMPLATE)
    failure_max = max((item.count for item in view.failure_breakdown), default=0)
    workflow_rows = tuple(sorted(view.workflow_breakdown, key=_workflow_sort_key))
    workflow_filters = sorted({item.workflow_type for item in view.results})
    failure_filters = sorted(
        {item.failure_kind for item in view.results if item.failure_kind is not None}
    )
    dominant_failure = view.failure_breakdown[0] if view.failure_breakdown else None
    top_failure = view.top_failures[0] if view.top_failures else None
    highlight_workflow = next(
        (row for row in workflow_rows if row.failed or row.errored),
        workflow_rows[0] if workflow_rows else None,
    )
    top_likely_cause = (
        top_failure.likely_cause
        if top_failure and top_failure.likely_cause
        else (
            "No likely cause classified."
            if view.failed
            else "No replay failures classified."
        )
    )
    top_remediation = (
        top_failure.remediation_hint
        if top_failure and top_failure.remediation_hint
        else (
            "No remediation hint classified."
            if view.failed
            else "No remediation required."
        )
    )
    diagnosis_heading = "Why this failed" if view.policy_decision == "fail" else "Why this passed"
    section_links = (
        {"id": "why-this-failed", "label": diagnosis_heading},
        {"id": "verification-summary", "label": "Verification Summary"},
        {"id": "workflow-type-breakdown", "label": "Affected Workflow Types"},
        {"id": "top-failing-histories", "label": "Top Failing Histories"},
        {"id": "all-results", "label": "All Results"},
        {"id": "advanced-details", "label": "Advanced Details"},
    )
    return template.render(
        view=view,
        diagnosis_heading=diagnosis_heading,
        dominant_failure=dominant_failure,
        failure_filters=failure_filters,
        failure_max=failure_max,
        highlight_workflow=highlight_workflow,
        section_links=section_links,
        top_likely_cause=top_likely_cause,
        top_remediation=top_remediation,
        workflow_filters=workflow_filters,
        workflow_rows=workflow_rows,
    )


def write_html_report(report: VerificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html_report(report), encoding="utf-8")
    return output_path
