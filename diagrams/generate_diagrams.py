#!/usr/bin/env python3
"""Generate all four blog diagrams as Excalidraw JSON files."""
import json
from pathlib import Path

DIR = Path(__file__).parent

# Color palette
PRIMARY_FILL = "#3b82f6"
PRIMARY_STROKE = "#1e3a5f"
SECONDARY_FILL = "#60a5fa"
SECONDARY_STROKE = "#1e3a5f"
TERTIARY_FILL = "#93c5fd"
TERTIARY_STROKE = "#1e3a5f"
START_FILL = "#fed7aa"
START_STROKE = "#c2410c"
END_FILL = "#a7f3d0"
END_STROKE = "#047857"
DECISION_FILL = "#fef3c7"
DECISION_STROKE = "#b45309"
AI_FILL = "#ddd6fe"
AI_STROKE = "#6d28d9"
ERROR_FILL = "#fecaca"
ERROR_STROKE = "#b91c1c"
WARNING_FILL = "#fee2e2"
WARNING_STROKE = "#dc2626"
CODE_BG = "#1e293b"
CODE_TEXT = "#22c55e"
TITLE_COLOR = "#1e40af"
SUBTITLE_COLOR = "#3b82f6"
BODY_COLOR = "#64748b"
TEXT_ON_LIGHT = "#374151"
TEXT_ON_DARK = "#ffffff"
ARROW_COLOR = "#1e3a5f"
LINE_COLOR = "#64748b"
DOT_FILL = "#3b82f6"

seed_counter = 1000

def next_seed():
    global seed_counter
    seed_counter += 1
    return seed_counter

def rect(id, x, y, w, h, fill, stroke, bound_text_id=None, round_type=3):
    be = [{"id": bound_text_id, "type": "text"}] if bound_text_id else []
    return {
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "angle": 0, "seed": next_seed(), "version": 1, "versionNonce": next_seed(),
        "isDeleted": False, "groupIds": [], "boundElements": be if be else None,
        "link": None, "locked": False, "roundness": {"type": round_type}
    }

def text(id, x, y, w, h, txt, size=16, color=TEXT_ON_LIGHT, align="center", valign="middle", container_id=None):
    return {
        "type": "text", "id": id, "x": x, "y": y, "width": w, "height": h,
        "text": txt, "originalText": txt, "fontSize": size, "fontFamily": 3,
        "textAlign": align, "verticalAlign": valign if container_id else "top",
        "strokeColor": color, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "angle": 0, "seed": next_seed(), "version": 1, "versionNonce": next_seed(),
        "isDeleted": False, "groupIds": [], "boundElements": None,
        "link": None, "locked": False, "containerId": container_id, "lineHeight": 1.25
    }

def arrow(id, x, y, pts, stroke=ARROW_COLOR, start_id=None, end_id=None, style="solid", width=2):
    sb = {"elementId": start_id, "focus": 0, "gap": 2} if start_id else None
    eb = {"elementId": end_id, "focus": 0, "gap": 2} if end_id else None
    w = max(abs(p[0]) for p in pts) if pts else 0
    h = max(abs(p[1]) for p in pts) if pts else 0
    return {
        "type": "arrow", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": width, "strokeStyle": style, "roughness": 0, "opacity": 100,
        "angle": 0, "seed": next_seed(), "version": 1, "versionNonce": next_seed(),
        "isDeleted": False, "groupIds": [], "boundElements": None,
        "link": None, "locked": False, "points": pts,
        "startBinding": sb, "endBinding": eb,
        "startArrowhead": None, "endArrowhead": "arrow"
    }

def ellipse(id, x, y, w, h, fill, stroke):
    return {
        "type": "ellipse", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "angle": 0, "seed": next_seed(), "version": 1, "versionNonce": next_seed(),
        "isDeleted": False, "groupIds": [], "boundElements": None,
        "link": None, "locked": False
    }

def diamond(id, x, y, w, h, fill, stroke, bound_text_id=None):
    be = [{"id": bound_text_id, "type": "text"}] if bound_text_id else []
    return {
        "type": "diamond", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "angle": 0, "seed": next_seed(), "version": 1, "versionNonce": next_seed(),
        "isDeleted": False, "groupIds": [], "boundElements": be if be else None,
        "link": None, "locked": False
    }

def wrap(elements):
    return {
        "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
        "files": {}
    }

def save(name, elements):
    # Post-process: ensure all arrow bindings are reflected in target elements' boundElements
    el_map = {e["id"]: e for e in elements}
    for e in elements:
        if e["type"] == "arrow":
            for binding_key in ("startBinding", "endBinding"):
                binding = e.get(binding_key)
                if binding and binding.get("elementId"):
                    target = el_map.get(binding["elementId"])
                    if target:
                        if target.get("boundElements") is None:
                            target["boundElements"] = []
                        existing_ids = {b["id"] for b in target["boundElements"]}
                        if e["id"] not in existing_ids:
                            target["boundElements"].append({"id": e["id"], "type": "arrow"})
    path = DIR / f"{name}.excalidraw"
    path.write_text(json.dumps(wrap(elements), indent=2))
    print(f"Created {path}")


# ============================================================
# DIAGRAM 1: Architecture Overview
# ============================================================
def diagram1():
    els = []
    # Title
    els.append(text("d1_title", 250, 20, 500, 35, "Task Analyzer Plugin — Architecture", 28, TITLE_COLOR, "center"))
    els.append(text("d1_subtitle", 250, 60, 500, 22, "End-to-end flow from Airflow UI to AI-powered analysis", 16, BODY_COLOR, "center"))

    # Step 1: User / Airflow UI
    els.append(ellipse("d1_user", 40, 160, 80, 80, START_FILL, START_STROKE))
    els.append(text("d1_user_t", 45, 185, 70, 30, "User\n(Airflow UI)", 14, TEXT_ON_LIGHT, "center"))

    # Arrow user -> plugin
    els.append(arrow("d1_a1", 122, 200, [[0, 0], [68, 0]], START_STROKE, "d1_user", "d1_plugin"))

    # Step 2: Plugin (FastAPI)
    els.append(rect("d1_plugin", 190, 150, 160, 100, PRIMARY_FILL, PRIMARY_STROKE, "d1_plugin_t"))
    els.append(text("d1_plugin_t", 195, 170, 150, 60, "Task Analyzer\nPlugin\n(FastAPI)", 14, TEXT_ON_DARK, "center", "middle", "d1_plugin"))

    # Arrow plugin -> gather
    els.append(arrow("d1_a2", 352, 200, [[0, 0], [58, 0]], PRIMARY_STROKE, "d1_plugin", "d1_gather"))

    # Step 3: Context Gathering
    els.append(rect("d1_gather", 410, 130, 180, 140, TERTIARY_FILL, TERTIARY_STROKE, "d1_gather_t"))
    els.append(text("d1_gather_t", 415, 155, 170, 90, "Context Gathering\n\nLogs\nDAG Source\nTask Metadata\nOperator Scripts", 13, TEXT_ON_LIGHT, "center", "middle", "d1_gather"))

    # Arrow gather -> bedrock
    els.append(arrow("d1_a3", 592, 200, [[0, 0], [58, 0]], PRIMARY_STROKE, "d1_gather", "d1_bedrock"))

    # Step 4: AWS Bedrock
    els.append(rect("d1_bedrock", 650, 150, 150, 100, AI_FILL, AI_STROKE, "d1_bedrock_t"))
    els.append(text("d1_bedrock_t", 655, 170, 140, 60, "AWS Bedrock\n\nClaude Models", 14, AI_STROKE, "center", "middle", "d1_bedrock"))

    # Arrow bedrock -> result
    els.append(arrow("d1_a4", 802, 200, [[0, 0], [58, 0]], AI_STROKE, "d1_bedrock", "d1_result"))

    # Step 5: Analysis Result
    els.append(rect("d1_result", 860, 150, 160, 100, END_FILL, END_STROKE, "d1_result_t"))
    els.append(text("d1_result_t", 865, 165, 150, 70, "Analysis Result\n\nRoot Cause\nFix Steps\nBest Practices", 13, TEXT_ON_LIGHT, "center", "middle", "d1_result"))

    # Bottom: evidence artifact showing prompt structure
    els.append(rect("d1_code_bg", 40, 310, 990, 60, CODE_BG, CODE_BG))
    els.append(text("d1_code", 50, 320, 970, 40,
        "Prompt:  { task_info, logs, dag_source, operator_script, errors }  →  Analysis",
        14, CODE_TEXT, "left", "top"))

    # Labels under each step
    els.append(text("d1_l1", 30, 250, 100, 18, "1. Click Analyze", 11, BODY_COLOR, "center"))
    els.append(text("d1_l2", 210, 260, 140, 18, "2. Route Request", 11, BODY_COLOR, "center"))
    els.append(text("d1_l3", 440, 280, 140, 18, "3. Gather Context", 11, BODY_COLOR, "center"))
    els.append(text("d1_l4", 670, 260, 120, 18, "4. Invoke LLM", 11, BODY_COLOR, "center"))
    els.append(text("d1_l5", 885, 260, 120, 18, "5. Return Results", 11, BODY_COLOR, "center"))

    save("01_architecture_overview", els)

# ============================================================
# DIAGRAM 2: Multi-Operator Script Analysis (Fan-Out)
# ============================================================
def diagram2():
    els = []
    els.append(text("d2_title", 200, 20, 600, 35, "Multi-Operator Script Analysis", 28, TITLE_COLOR, "center"))
    els.append(text("d2_sub", 200, 58, 600, 20, "Automatic detection and script fetching for 8 operator types", 15, BODY_COLOR, "center"))

    # Center: Script Detector (true center of diagram)
    cx, cy = 500, 270
    els.append(rect("d2_hub", cx-90, cy-45, 180, 90, PRIMARY_FILL, PRIMARY_STROKE, "d2_hub_t"))
    els.append(text("d2_hub_t", cx-85, cy-30, 170, 60, "Script Detector\n\nAuto-detect\noperator type", 13, TEXT_ON_DARK, "center", "middle", "d2_hub"))

    # Left side: 3 source boxes
    sources = [
        ("S3 Scripts", "Glue / EMR", SECONDARY_FILL, SECONDARY_STROKE),
        ("Inline SQL", "Athena / Redshift", DECISION_FILL, DECISION_STROKE),
        ("Inline Code", "Bash / Python / DBT", START_FILL, START_STROKE),
    ]
    src_x, src_w = 40, 170
    merge_x = 310  # X where the 3 arrows merge into one
    for i, (label, sub, fill, stroke) in enumerate(sources):
        sy = 150 + i * 100
        rid = f"d2_src_{i}"
        tid = f"d2_src_t_{i}"
        els.append(rect(rid, src_x, sy, src_w, 65, fill, stroke, tid))
        els.append(text(tid, src_x+5, sy+6, src_w-10, 52, f"{label}\n{sub}", 13, TEXT_ON_LIGHT, "center", "middle", rid))
        # Short arrow from source right edge to merge point X, converging to cy
        src_right = src_x + src_w
        src_cy = sy + 32
        els.append(arrow(f"d2_sa_{i}", src_right, src_cy, [[0, 0], [merge_x - src_right, cy - src_cy]], stroke, None, None))

    # Merge dot at convergence point
    els.append(ellipse("d2_merge_dot", merge_x - 6, cy - 6, 12, 12, DOT_FILL, PRIMARY_STROKE))

    # Single arrow from merge point to hub left edge
    hub_left = cx - 90
    els.append(arrow("d2_merge_arrow", merge_x + 6, cy, [[0, 0], [hub_left - merge_x - 10, 0]], PRIMARY_STROKE, None, None))

    # Right side: Fan-out to processing steps
    outputs = [
        ("Fetch from S3", "via Glue/S3 API", SECONDARY_FILL, SECONDARY_STROKE),
        ("Extract Inline", "from rendered_fields", DECISION_FILL, DECISION_STROKE),
        ("Sanitize", "Remove credentials", WARNING_FILL, WARNING_STROKE),
        ("Truncate", "Max 20KB", TERTIARY_FILL, TERTIARY_STROKE),
    ]
    hub_right = cx + 90  # 590
    out_x = 750
    arrow_start_ys = [cy - 30, cy - 10, cy + 10, cy + 30]
    for i, (label, sub, fill, stroke) in enumerate(outputs):
        oy = 120 + i * 85
        out_cy = oy + 32
        rid = f"d2_out_{i}"
        tid = f"d2_out_t_{i}"
        els.append(rect(rid, out_x, oy, 170, 65, fill, stroke, tid))
        els.append(text(tid, out_x+5, oy+6, 160, 52, f"{label}\n{sub}", 13, TEXT_ON_LIGHT, "center", "middle", rid))
        start_y = arrow_start_ys[i]
        dx = out_x - hub_right - 4
        dy = out_cy - start_y
        if i >= 2:
            mid_x = 680
            els.append(arrow(f"d2_oa_{i}", hub_right, start_y,
                [[0, 0], [mid_x - hub_right, 0], [dx, dy]],
                PRIMARY_STROKE, None, None))
        else:
            els.append(arrow(f"d2_oa_{i}", hub_right, start_y, [[0, 0], [dx, dy]], PRIMARY_STROKE, None, None))

    # Final arrow: Truncate -> Send to Claude
    els.append(rect("d2_llm", out_x, 470, 170, 60, AI_FILL, AI_STROKE, "d2_llm_t"))
    els.append(text("d2_llm_t", out_x+5, 478, 160, 44, "Send to Claude\nwith full context", 13, AI_STROKE, "center", "middle", "d2_llm"))
    els.append(arrow("d2_llm_a", out_x + 85, 380, [[0, 0], [0, 86]], PRIMARY_STROKE, None, None))

    # Operator badges at bottom
    ops = ["Glue", "EMR", "EMR\nServerless", "Athena", "Redshift", "Bash", "Python", "DBT"]
    for i, op in enumerate(ops):
        ox = 60 + i * 110
        rid = f"d2_op_{i}"
        tid = f"d2_op_t_{i}"
        bh = 40
        by = 550
        els.append(rect(rid, ox, by, 90, bh, TERTIARY_FILL, TERTIARY_STROKE, tid))
        # Center text vertically: rect_y + (rect_h - text_h) / 2
        th = 30
        ty = by + (bh - th) // 2
        els.append(text(tid, ox+2, ty, 86, th, op, 11, TEXT_ON_LIGHT, "center", "middle", rid))

    els.append(text("d2_ops_label", 350, 530, 200, 16, "Supported Operators", 12, SUBTITLE_COLOR, "center"))

    save("02_multi_operator_analysis", els)

# ============================================================
# DIAGRAM 4: What the LLM Receives (Convergence)
# ============================================================
def diagram4():
    els = []
    els.append(text("d4_title", 200, 15, 550, 35, "What the LLM Receives", 28, TITLE_COLOR, "center"))
    els.append(text("d4_sub", 200, 52, 550, 20, "All context pieces converge into a single enriched prompt", 15, BODY_COLOR, "center"))

    # Left: input sources (stacked)
    inputs = [
        ("Task Metadata", "DAG ID, Task ID, State\nOperator, Try Number", START_FILL, START_STROKE),
        ("Execution Logs", "Full stdout/stderr\nStack traces, errors", ERROR_FILL, ERROR_STROKE),
        ("DAG Source Code", "Complete Python DAG\ndefinition file", PRIMARY_FILL, PRIMARY_STROKE),
        ("Operator Script", "Glue/EMR/Bash/SQL\nfetched automatically", DECISION_FILL, DECISION_STROKE),
        ("Error Context", "Exception type, message\nFailing line number", WARNING_FILL, WARNING_STROKE),
    ]

    for i, (label, sub, fill, stroke) in enumerate(inputs):
        iy = 100 + i * 85
        rid = f"d4_in_{i}"
        tid = f"d4_in_t_{i}"
        els.append(rect(rid, 40, iy, 200, 65, fill, stroke, tid))
        els.append(text(tid, 45, iy+6, 190, 52, f"{label}\n{sub}", 12, TEXT_ON_LIGHT, "center", "middle", rid))
        els.append(arrow(f"d4_ia_{i}", 242, iy+32, [[0, 0], [88, 295 - iy]], stroke, rid, "d4_prompt"))

    # Center: Prompt assembly
    els.append(rect("d4_prompt", 330, 180, 200, 110, AI_FILL, AI_STROKE, "d4_prompt_t"))
    els.append(text("d4_prompt_t", 335, 195, 190, 80, "Prompt Assembly\n\nStructured prompt\nwith all context\n(~16K-26K tokens)", 12, AI_STROKE, "center", "middle", "d4_prompt"))

    # Arrow to Bedrock
    els.append(arrow("d4_a_bedrock", 532, 235, [[0, 0], [78, 0]], AI_STROKE, "d4_prompt", "d4_bedrock"))

    # Bedrock
    els.append(rect("d4_bedrock", 610, 200, 150, 70, AI_FILL, AI_STROKE, "d4_bedrock_t"))
    els.append(text("d4_bedrock_t", 615, 210, 140, 50, "AWS Bedrock\nClaude", 14, AI_STROKE, "center", "middle", "d4_bedrock"))

    # Arrow to output
    els.append(arrow("d4_a_out", 762, 235, [[0, 0], [68, 0]], END_STROKE, "d4_bedrock", "d4_output"))

    # Output
    els.append(rect("d4_output", 830, 160, 170, 150, END_FILL, END_STROKE, "d4_output_t"))
    els.append(text("d4_output_t", 835, 175, 160, 120, "Structured Analysis\n\nRoot Cause\nDetailed Explanation\nFix Recommendations\nBest Practices\nPrevention Tips", 12, TEXT_ON_LIGHT, "center", "middle", "d4_output"))

    # Token usage evidence artifact at bottom
    els.append(rect("d4_token_bg", 40, 530, 960, 65, CODE_BG, CODE_BG))
    els.append(text("d4_token", 50, 538, 940, 50,
        "Token Budget:  Task ~1K  +  Logs ~10K  +  DAG ~500  +  Script ~5-15K  =  ~16.5-26.5K tokens  (8-13% of 200K limit)",
        13, CODE_TEXT, "left", "top"))

    # Model options
    els.append(text("d4_models_label", 610, 290, 150, 16, "Available Models", 12, SUBTITLE_COLOR, "center"))
    models = ["Sonnet 3.5", "Sonnet 4.5", "Sonnet 4.6", "Opus 4.6"]
    for i, m in enumerate(models):
        mx = 570 + i * 110
        rid = f"d4_m_{i}"
        tid = f"d4_m_t_{i}"
        els.append(rect(rid, mx, 310, 95, 35, TERTIARY_FILL, TERTIARY_STROKE, tid))
        els.append(text(tid, mx+2, 315, 91, 25, m, 11, TEXT_ON_LIGHT, "center", "middle", rid))

    save("04_llm_context_convergence", els)


if __name__ == "__main__":
    diagram1()
    diagram2()
    diagram4()
    print("All diagrams generated!")
