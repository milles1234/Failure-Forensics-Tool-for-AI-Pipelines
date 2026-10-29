# pages/_trace_explorer.py
"""
Trace Explorer -- interactive pipeline graph view for Failure Forensics Tool.

Renders each pipeline step as a node, color-coded by health status:
  - Green  -- healthy  (confidence >= 4, no error)
  - Yellow -- low confidence  (confidence 3, or suspect step)
  - Red    -- root cause  (confidence <= 2, or has error)

Clicking a node button reveals the full span details panel.
"""

import json
import os
import glob
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# -- paths ---------------------------------------------------------------------
TRACES_DIR = Path(__file__).parent.parent.parent / "data" / "traces"

STEP_LABELS = {
    "step_1_intake":         ("📥", "Intake"),
    "step_2_extraction":     ("🔍", "Extraction"),
    "step_3_classification": ("🏷️", "Classification"),
    "step_4_summarization":  ("📝", "Summarization"),
}


# -- helpers -------------------------------------------------------------------

def load_traces() -> list:
    """Load all JSON trace files from the traces directory."""
    traces = []
    for fp in sorted(glob.glob(str(TRACES_DIR / "*.json"))):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
                data["_file"] = os.path.basename(fp)
                traces.append(data)
        except Exception as e:
            st.warning(f"Could not load {fp}: {e}")
    return traces


def node_status(span: dict, root_cause_step) -> str:
    """Classify a span as 'healthy', 'suspect', or 'root_cause'."""
    if span["step_name"] == root_cause_step:
        return "root_cause"
    score = span.get("confidence_score")
    if span.get("error"):
        return "root_cause"
    if score is not None and score <= 2:
        return "root_cause"
    if score is not None and score == 3:
        return "suspect"
    return "healthy"


def build_graph_html(spans: list, root_cause_step, selected_idx) -> str:
    """
    Returns an HTML/JS string with an animated SVG pipeline graph.
    Color-coded by node status with pulse effects on root-cause nodes.
    """
    STATUS_COLORS = {
        "healthy":    {"fill": "#1DB954", "glow": "#1DB95488", "ring": "#25e668"},
        "suspect":    {"fill": "#F59E0B", "glow": "#F59E0B88", "ring": "#fbbf24"},
        "root_cause": {"fill": "#EF4444", "glow": "#EF444488", "ring": "#f87171"},
    }
    STATUS_LABELS = {
        "healthy":    "Healthy",
        "suspect":    "Low Confidence",
        "root_cause": "Root Cause",
    }

    node_data = []
    for i, span in enumerate(spans):
        status = node_status(span, root_cause_step)
        icon, label = STEP_LABELS.get(span["step_name"], ("⚙️", span["step_name"]))
        score = span.get("confidence_score")
        latency = span.get("latency_ms", 0)
        node_data.append({
            "idx": i,
            "label": label,
            "icon": icon,
            "step_name": span["step_name"],
            "status": status,
            "score": score,
            "latency": latency,
            "colors": STATUS_COLORS[status],
            "statusLabel": STATUS_LABELS[status],
        })

    nodes_json = json.dumps(node_data)
    selected_json = json.dumps(selected_idx)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: transparent; font-family: 'Inter', 'Segoe UI', sans-serif; overflow: hidden; }}
#canvas {{ width: 100%; height: 210px; position: relative; }}
svg {{ width: 100%; height: 210px; overflow: visible; }}
.node-group {{ cursor: pointer; }}
.node-group:hover .node-circle {{ filter: brightness(1.3); transition: filter 0.2s; }}
.connector {{ stroke-dasharray: 6 3; animation: dash 1.5s linear infinite; }}
@keyframes dash {{ to {{ stroke-dashoffset: -18; }} }}
.legend {{ display: flex; gap: 18px; justify-content: center; padding: 8px 0 0 0; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: #94a3b8; font-family: 'Inter', sans-serif; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
</style>
</head>
<body>
<div id="canvas">
  <svg id="pipeline-svg" viewBox="0 0 800 200" preserveAspectRatio="xMidYMid meet">
    <defs>
      <filter id="drop-shadow">
        <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00000055"/>
      </filter>
    </defs>
    <g id="graph-root"></g>
  </svg>
</div>
<div class="legend">
  <div class="legend-item">
    <div class="legend-dot" style="background:#1DB954;box-shadow:0 0 6px #1DB954;"></div>
    <span>Healthy</span>
  </div>
  <div class="legend-item">
    <div class="legend-dot" style="background:#F59E0B;box-shadow:0 0 6px #F59E0B;"></div>
    <span>Low Confidence</span>
  </div>
  <div class="legend-item">
    <div class="legend-dot" style="background:#EF4444;box-shadow:0 0 6px #EF4444;"></div>
    <span>Root Cause</span>
  </div>
</div>
<script>
const nodes = {nodes_json};
const selectedIdx = {selected_json};
const svgWidth = 800;
const nodeCount = nodes.length;
const padding = 90;
const stepW = (svgWidth - padding * 2) / Math.max(nodeCount - 1, 1);
const cy = 95;
const r = 38;
const svg = document.getElementById('graph-root');

// Connectors
for (let i = 0; i < nodeCount - 1; i++) {{
  const x1 = padding + i * stepW + r;
  const x2 = padding + (i + 1) * stepW - r;
  const sA = nodes[i].status;
  const sB = nodes[i + 1].status;
  const cc = (sA === 'root_cause' || sB === 'root_cause') ? '#EF4444'
    : (sA === 'suspect' || sB === 'suspect') ? '#F59E0B' : '#1DB954';
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', x1); line.setAttribute('y1', cy);
  line.setAttribute('x2', x2); line.setAttribute('y2', cy);
  line.setAttribute('stroke', cc); line.setAttribute('stroke-width', '2.5');
  line.setAttribute('stroke-opacity', '0.5'); line.classList.add('connector');
  svg.appendChild(line);
  const ax = x2 + 2;
  const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
  poly.setAttribute('points', `${{ax}},${{cy}} ${{ax-8}},${{cy-5}} ${{ax-8}},${{cy+5}}`);
  poly.setAttribute('fill', cc); poly.setAttribute('opacity', '0.75');
  svg.appendChild(poly);
}}

// Nodes
nodes.forEach((node, i) => {{
  const cx = padding + i * stepW;
  const isSel = (i === selectedIdx);
  const col = node.colors;
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.classList.add('node-group');

  // Pulse for root cause
  if (node.status === 'root_cause') {{
    const pulse = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    pulse.setAttribute('cx', cx); pulse.setAttribute('cy', cy); pulse.setAttribute('r', r + 8);
    pulse.setAttribute('fill', col.glow);
    pulse.innerHTML = `<animate attributeName="r" values="${{r+6}};${{r+18}};${{r+6}}" dur="2s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.4;0.05;0.4" dur="2s" repeatCount="indefinite"/>`;
    svg.appendChild(pulse);
  }}

  // Selection ring
  if (isSel) {{
    const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    ring.setAttribute('cx', cx); ring.setAttribute('cy', cy); ring.setAttribute('r', r + 7);
    ring.setAttribute('fill', 'none'); ring.setAttribute('stroke', col.ring);
    ring.setAttribute('stroke-width', '2.5'); ring.setAttribute('stroke-dasharray', '6 4');
    g.appendChild(ring);
  }}

  // Main circle
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('cx', cx); circle.setAttribute('cy', cy); circle.setAttribute('r', r);
  circle.setAttribute('fill', col.fill); circle.setAttribute('filter', 'url(#drop-shadow)');
  circle.setAttribute('opacity', isSel ? '1' : '0.88'); circle.classList.add('node-circle');
  g.appendChild(circle);

  // Gloss
  const gloss = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
  gloss.setAttribute('cx', cx - 6); gloss.setAttribute('cy', cy - 10);
  gloss.setAttribute('rx', 14); gloss.setAttribute('ry', 8);
  gloss.setAttribute('fill', 'white'); gloss.setAttribute('opacity', '0.12');
  g.appendChild(gloss);

  // Icon
  const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  icon.setAttribute('x', cx); icon.setAttribute('y', cy - 2);
  icon.setAttribute('text-anchor', 'middle'); icon.setAttribute('dominant-baseline', 'central');
  icon.setAttribute('font-size', '22'); icon.style.pointerEvents = 'none';
  icon.textContent = node.icon; g.appendChild(icon);

  // Score badge
  if (node.score !== null && node.score !== undefined) {{
    const sc = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    sc.setAttribute('cx', cx + r - 5); sc.setAttribute('cy', cy - r + 5);
    sc.setAttribute('r', 13); sc.setAttribute('fill', '#0f172a');
    sc.setAttribute('stroke', col.ring); sc.setAttribute('stroke-width', '1.5');
    g.appendChild(sc);
    const st = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    st.setAttribute('x', cx + r - 5); st.setAttribute('y', cy - r + 5);
    st.setAttribute('text-anchor', 'middle'); st.setAttribute('dominant-baseline', 'central');
    st.setAttribute('font-size', '9'); st.setAttribute('font-weight', '800');
    st.setAttribute('fill', col.ring); st.style.pointerEvents = 'none';
    st.textContent = node.score + '/5'; g.appendChild(st);
  }}

  // Label
  const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  lbl.setAttribute('x', cx); lbl.setAttribute('y', cy + r + 16);
  lbl.setAttribute('text-anchor', 'middle'); lbl.setAttribute('font-size', '12');
  lbl.setAttribute('font-weight', '600'); lbl.setAttribute('fill', '#cbd5e1');
  lbl.style.pointerEvents = 'none'; lbl.textContent = node.label; g.appendChild(lbl);

  // Latency
  const lat = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  lat.setAttribute('x', cx); lat.setAttribute('y', cy + r + 30);
  lat.setAttribute('text-anchor', 'middle'); lat.setAttribute('font-size', '10');
  lat.setAttribute('fill', '#64748b'); lat.style.pointerEvents = 'none';
  lat.textContent = node.latency ? node.latency.toFixed(0) + 'ms' : ''; g.appendChild(lat);

  svg.appendChild(g);
}});
</script>
</body>
</html>"""


def render_span_detail(span: dict, root_cause_step, root_cause_analysis):
    """Renders the full detail panel for a selected span."""
    status = node_status(span, root_cause_step)
    icon, label = STEP_LABELS.get(span["step_name"], ("⚙️", span["step_name"]))

    STATUS_CONFIG = {
        "healthy":    {"color": "#1DB954", "bg": "#0f2a1a", "badge": "✅ Healthy",          "border": "#1DB95433"},
        "suspect":    {"color": "#F59E0B", "bg": "#2a1f0a", "badge": "⚠️ Low Confidence",  "border": "#F59E0B33"},
        "root_cause": {"color": "#EF4444", "bg": "#2a0f0f", "badge": "🚨 Root Cause",       "border": "#EF444433"},
    }
    cfg = STATUS_CONFIG[status]

    # Header card
    st.markdown(f"""
    <div style="background:{cfg['bg']};border:1px solid {cfg['border']};border-left:4px solid {cfg['color']};
    border-radius:12px;padding:20px 24px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:32px;">{icon}</span>
        <div>
          <div style="font-size:20px;font-weight:700;color:#f1f5f9;">{label}</div>
          <div style="font-size:12px;color:#94a3b8;font-family:monospace;">{span['step_name']}</div>
        </div>
        <span style="margin-left:auto;background:{cfg['color']}22;border:1px solid {cfg['color']}66;
        color:{cfg['color']};padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;">
          {cfg['badge']}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Metrics
    score = span.get("confidence_score")
    latency = span.get("latency_ms", 0) or 0
    prompt_tok = span.get("prompt_tokens")
    comp_tok = span.get("completion_tokens")

    mc1, mc2, mc3, mc4 = st.columns(4)
    score_color = "#1DB954" if (score or 0) >= 4 else "#F59E0B" if (score or 0) == 3 else "#EF4444"
    score_txt = f"{score}/5" if score is not None else "N/A"

    with mc1:
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
          <div style="font-size:26px;font-weight:800;color:{score_color};">{score_txt}</div>
          <div style="font-size:10px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;">Confidence</div>
        </div>""", unsafe_allow_html=True)
    with mc2:
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
          <div style="font-size:26px;font-weight:800;color:#60a5fa;">{latency:.0f}<span style="font-size:13px;">ms</span></div>
          <div style="font-size:10px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;">Latency</div>
        </div>""", unsafe_allow_html=True)
    with mc3:
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
          <div style="font-size:26px;font-weight:800;color:#a78bfa;">{prompt_tok if prompt_tok else "—"}</div>
          <div style="font-size:10px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;">Prompt Tokens</div>
        </div>""", unsafe_allow_html=True)
    with mc4:
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
          <div style="font-size:26px;font-weight:800;color:#34d399;">{comp_tok if comp_tok else "—"}</div>
          <div style="font-size:10px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;">Completion Tokens</div>
        </div>""", unsafe_allow_html=True)

    # Span metadata bar
    span_id = span.get("span_id", "—")
    start = span.get("start_time", "—")
    end = span.get("end_time", "—")
    st.markdown(f"""<div style="background:#0f172a;border-radius:8px;padding:10px 16px;margin:12px 0;
    font-family:monospace;font-size:11px;color:#64748b;line-height:2;">
      <span style="color:#475569;">span_id:</span> <span style="color:#94a3b8;">{span_id}</span>
      &nbsp;&nbsp;|&nbsp;&nbsp;
      <span style="color:#475569;">start:</span> <span style="color:#94a3b8;">{start}</span>
      &nbsp;&nbsp;|&nbsp;&nbsp;
      <span style="color:#475569;">end:</span> <span style="color:#94a3b8;">{end}</span>
    </div>""", unsafe_allow_html=True)

    # Error banner
    if span.get("error"):
        st.error(f"**Error captured:** {span['error']}")

    # LLM-as-Judge verdict
    judgment = span.get("judgment")
    if judgment:
        st.markdown("---")
        st.markdown("#### 🔬 LLM-as-Judge Verdict")
        jc1, jc2 = st.columns([1, 2])
        reasonable = judgment.get("is_reasonable_transformation", False)
        quality = judgment.get("quality_score", "—")
        failure_type = judgment.get("failure_type", "—")
        reasoning = judgment.get("reasoning", "—")
        with jc1:
            r_str = "✅ Yes" if reasonable else "❌ No"
            st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;height:160px;">
              <div style="margin-bottom:12px;">
                <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Reasonable Transform</div>
                <div style="font-size:18px;font-weight:700;">{r_str}</div>
              </div>
              <div style="margin-bottom:12px;">
                <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Quality Score</div>
                <div style="font-size:18px;font-weight:700;color:#F59E0B;">{quality}/5</div>
              </div>
              <div>
                <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Failure Type</div>
                <div style="font-size:13px;font-weight:600;color:#f87171;">{failure_type}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        with jc2:
            st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;min-height:160px;">
              <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Judge Reasoning</div>
              <div style="color:#e2e8f0;font-size:13px;line-height:1.7;">{reasoning}</div>
            </div>""", unsafe_allow_html=True)

    # Root cause highlight
    if root_cause_analysis and span["step_name"] == root_cause_analysis.get("root_cause_step"):
        st.markdown("---")
        st.markdown("#### 🚨 Root Cause Analysis")
        cat = root_cause_analysis.get("failure_category", "Unknown")
        expl = root_cause_analysis.get("explanation", "—")
        st.markdown(f"""<div style="background:#2a0f0f;border:1px solid #EF444433;border-left:4px solid #EF4444;
        border-radius:10px;padding:16px;">
          <div style="color:#f87171;font-weight:700;font-size:14px;margin-bottom:8px;">{cat}</div>
          <div style="color:#fca5a5;font-size:13px;line-height:1.6;">{expl}</div>
        </div>""", unsafe_allow_html=True)

    # Input / Output tabs
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    tab_in, tab_out = st.tabs(["📨 Input Data", "📤 Output Data"])
    with tab_in:
        st.json(span.get("input_data", {}))
    with tab_out:
        out = span.get("output_data")
        if out:
            st.json(out)
        else:
            st.markdown("*No output captured for this span.*")


# -- main page -----------------------------------------------------------------

def render():
    st.set_page_config(
        page_title="Trace Explorer | Failure Forensics",
        page_icon="🔭",
        layout="wide",
    )

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%);
    border:1px solid #312e81;border-radius:16px;padding:28px 32px;margin-bottom:24px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:-40%;right:-5%;width:280px;height:280px;
      background:radial-gradient(circle,#6366f133 0%,transparent 70%);pointer-events:none;"></div>
      <div style="font-size:28px;font-weight:800;background:linear-gradient(135deg,#818cf8,#c084fc,#60a5fa);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;">
        🔭 Trace Explorer
      </div>
      <div style="color:#64748b;font-size:14px;">
        Visualize AI pipeline execution flow &nbsp;·&nbsp; Color-coded by status &nbsp;·&nbsp; Click a step to inspect its span
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Load traces
    traces = load_traces()
    if not traces:
        st.warning("📂 No trace files found in `data/traces/`. Run the pipeline to generate traces.")
        return

    # Trace selector
    col_sel, col_badge = st.columns([3, 1])
    with col_sel:
        trace_options = {
            f"{t.get('trace_id','?')}  —  {t.get('status','?').upper()}  —  {t.get('_file','')}": t
            for t in traces
        }
        chosen_label = st.selectbox("Trace", list(trace_options.keys()), label_visibility="collapsed")

    trace = trace_options[chosen_label]
    trace_status = trace.get("status", "unknown")

    with col_badge:
        STATUS_MAP = {
            "success":  ("#1DB954", "#0f2a1a", "✅ SUCCESS"),
            "failed":   ("#EF4444", "#2a0f0f", "🚨 FAILED"),
            "degraded": ("#F59E0B", "#2a1f0a", "⚠️ DEGRADED"),
            "running":  ("#60a5fa", "#0a1f2a", "🔄 RUNNING"),
        }
        sc, sbg, sl = STATUS_MAP.get(trace_status, ("#94a3b8", "#1e293b", f"❓ {trace_status.upper()}"))
        st.markdown(f"""<div style="background:{sbg};border:1px solid {sc}33;border-radius:8px;
        padding:10px;text-align:center;margin-top:2px;">
          <span style="color:{sc};font-weight:700;font-size:13px;">{sl}</span>
        </div>""", unsafe_allow_html=True)

    spans = trace.get("spans", [])
    rca = trace.get("root_cause_analysis")
    root_cause_step = rca.get("root_cause_step") if rca else None

    # Trace-level metrics
    total_lat = trace.get("total_latency_ms", 0) or 0
    trace_score = trace.get("confidence_score")
    span_count = len(spans)
    suspect_count = sum(
        1 for s in spans
        if s.get("error") or (s.get("confidence_score") is not None and s["confidence_score"] <= 2)
    )

    tm1, tm2, tm3, tm4 = st.columns(4)
    with tm1:
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px;text-align:center;margin-bottom:14px;">
          <div style="font-size:22px;font-weight:800;color:#60a5fa;">{total_lat:.0f}<span style="font-size:12px;color:#64748b;">ms</span></div>
          <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Total Latency</div>
        </div>""", unsafe_allow_html=True)
    with tm2:
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px;text-align:center;margin-bottom:14px;">
          <div style="font-size:22px;font-weight:800;color:#a78bfa;">{span_count}</div>
          <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Pipeline Steps</div>
        </div>""", unsafe_allow_html=True)
    with tm3:
        sc2 = "#1DB954" if (trace_score or 0) >= 4 else "#F59E0B" if (trace_score or 0) == 3 else "#EF4444"
        ts_txt = f"{trace_score}/5" if trace_score else "—"
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px;text-align:center;margin-bottom:14px;">
          <div style="font-size:22px;font-weight:800;color:{sc2};">{ts_txt}</div>
          <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Trace Score</div>
        </div>""", unsafe_allow_html=True)
    with tm4:
        fc = "#EF4444" if suspect_count > 0 else "#1DB954"
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px;text-align:center;margin-bottom:14px;">
          <div style="font-size:22px;font-weight:800;color:{fc};">{suspect_count}</div>
          <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Suspect Steps</div>
        </div>""", unsafe_allow_html=True)

    # Initialize session state
    trace_key = trace.get("trace_id", "default")
    state_key = f"sel_span_{trace_key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    sel_idx = st.session_state[state_key]

    # Graph container
    st.markdown("""<div style="background:linear-gradient(135deg,#0f172a,#1a1f35);border:1px solid #1e293b;
    border-radius:16px;padding:24px;margin-bottom:16px;">
      <div style="font-size:12px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
        Pipeline Flow
      </div>""", unsafe_allow_html=True)

    graph_html = build_graph_html(spans, root_cause_step, sel_idx)
    components.html(graph_html, height=255, scrolling=False)

    # Node selector buttons
    st.markdown("<div style='margin-top:4px;margin-bottom:4px;font-size:12px;color:#475569;'>Select a step to inspect:</div>",
                unsafe_allow_html=True)
    btn_cols = st.columns(len(spans))
    for i, span in enumerate(spans):
        icon, label = STEP_LABELS.get(span["step_name"], ("⚙️", span["step_name"]))
        s_status = node_status(span, root_cause_step)
        dot = {"healthy": "🟢", "suspect": "🟡", "root_cause": "🔴"}.get(s_status, "⚪")
        with btn_cols[i]:
            is_active = (sel_idx == i)
            if st.button(f"{dot} {icon} {label}", key=f"node_btn_{trace_key}_{i}",
                         use_container_width=True, type="primary" if is_active else "secondary"):
                if sel_idx == i:
                    st.session_state[state_key] = None
                else:
                    st.session_state[state_key] = i
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Span detail panel
    st.markdown("---")
    st.markdown("### 🔍 Span Details")

    current_sel = st.session_state[state_key]
    if current_sel is None or current_sel >= len(spans):
        st.markdown("""<div style="background:#1e293b;border:1px dashed #334155;border-radius:12px;
        padding:48px;text-align:center;color:#475569;">
          <div style="font-size:40px;margin-bottom:12px;">🕵️</div>
          <div style="font-size:16px;font-weight:600;color:#334155;">No step selected</div>
          <div style="font-size:13px;margin-top:6px;">Click a step button above to inspect its full span details</div>
        </div>""", unsafe_allow_html=True)
    else:
        render_span_detail(spans[current_sel], root_cause_step, rca)

    # Root cause summary
    if rca:
        st.markdown("---")
        st.markdown("### 🧠 Root Cause Summary")
        rc_step = rca.get("root_cause_step", "—")
        rc_cat = rca.get("failure_category", "—")
        rc_expl = rca.get("explanation", "—")
        st.markdown(f"""<div style="background:linear-gradient(135deg,#2a0f0f,#1a0a1a);
        border:1px solid #EF444433;border-left:5px solid #EF4444;border-radius:12px;padding:20px 24px;">
          <div style="font-size:16px;font-weight:700;color:#f87171;margin-bottom:8px;">
            🚨 Root cause pinpointed:
            <code style="background:#ffffff11;padding:2px 8px;border-radius:4px;font-size:14px;">{rc_step}</code>
          </div>
          <div style="font-size:13px;color:#fca5a5;margin-bottom:14px;line-height:1.7;">{rc_expl}</div>
          <span style="background:#EF444422;border:1px solid #EF444444;color:#f87171;
          padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;">
            Category: {rc_cat}
          </span>
        </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
