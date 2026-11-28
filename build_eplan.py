#!/usr/bin/env python3
"""Generate eplan.html from eplan_data.yaml."""
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
YAML_PATH = ROOT / "eplan_data.yaml"
OUT_PATH = ROOT / "eplan.html"


def load_yaml(path: Path) -> dict:
    raw = subprocess.check_output(
        ["ruby", "-ryaml", "-rjson", "-e", "puts JSON.generate(YAML.safe_load(File.read(ARGV[0])))", str(path)],
        text=True,
    )
    return json.loads(raw)


def format_bullet_text(text: str) -> str:
    escaped = html.escape(text)
    m = re.match(r"^(\d{1,2}:\d{2}(?:am|pm)|Registration Desk:|2:30pm:|3:30pm:)(.*)$", escaped)
    if m:
        prefix = m.group(1)
        return f"<strong>{prefix}</strong>{m.group(2)}"
    return escaped


def format_item_text(text: str) -> str:
    escaped = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def render_items(items: list, ordered: bool = False, indent: int = 10) -> str:
    tag = "ol" if ordered else "ul"
    attrs = ' style="padding-left:18px;margin-top:4px;"' if ordered else ""
    pad = " " * indent
    lines = [f"{pad}<{tag}{attrs}>"]
    for it in items:
        parts = []
        status = (it.get("status") or "").strip().lower()
        if status == "done":
            parts.append('<span class="badge b-done">Done</span>')
        elif status == "open":
            parts.append('<span class="badge b-open">Open</span>')
        if it.get("label"):
            parts.append(f"<strong>{html.escape(it['label'])}</strong>")
        item_text = it.get("item") if it.get("item") is not None else it.get("text")
        if item_text:
            parts.append(format_item_text(str(item_text)))
        line = f"{pad}  <li>" + " ".join(parts)
        subitems = it.get("sub_items") or it.get("subitems")
        if subitems:
            sub = render_items(subitems, ordered=it.get("ordered", False), indent=indent + 4)
            line += f"\n{sub}\n{pad}  </li>"
        else:
            line += "</li>"
        lines.append(line)
    lines.append(f"{pad}</{tag}>")
    return "\n".join(lines)


def build() -> None:
    data = load_yaml(YAML_PATH)
    current_html = OUT_PATH.read_text(encoding="utf-8")

    head_prefix = current_html[: current_html.index("  <!-- Family Filter Bar -->")]
    top_banner = current_html[
        current_html.index("  <!-- ==================== TOP PORTION ==================== -->") : current_html.index(
            '<div class="schedule-grid">'
        )
    ]
    script_suffix = current_html[current_html.index("  <script>") :]

    families = data["families"]
    schedule = data["schedule"]
    action_items = data["action_items"]

    # Build Family Filter Bar
    filter_lines = [
        "  <!-- Family Filter Bar -->",
        '  <div class="mobile-filter" aria-label="Filter by family">',
        '    <button type="button" class="active" data-filter="all">All</button>',
    ]
    for fam in families:
        short_name = fam.get("short_name") or fam["name"].split("&")[0].strip()
        filter_lines.append(
            f'    <button type="button" data-filter="{html.escape(str(fam["id"]))}">{html.escape(short_name)}</button>'
        )
    filter_lines.append("  </div>")
    filter_lines.append("")

    # Build Schedule Grid
    sg_lines = ['<div class="schedule-grid">', '    <div class="cell col-header h-time">Time Slot</div>']
    for fam in families:
        sg_lines.append(
            f'    <div class="cell col-header {fam["header_class"]}" data-family="{fam["id"]}">{html.escape(fam["name"])}</div>'
        )

    for row in schedule:
        time_parts = row["time"].split(" – ")
        time_disp = "<br>–<br>".join(html.escape(p.strip()) for p in time_parts)
        sg_lines.append(f'    <div class="cell time-cell">\n      {time_disp}\n    </div>')
        for fam in families:
            fid = str(fam["id"])
            bg_cls = fam["header_class"].replace("h-", "bg-")
            fam_name = html.escape(fam["name"])
            content = row["cells"].get(fid)
            if not content:
                sg_lines.append(
                    f'    <div class="cell {bg_cls}" data-family="{fid}" data-empty="true">\n'
                    f'      <div class="mobile-fam-title">{fam_name}</div>\n'
                    f'      <ul><li>—</li></ul>\n'
                    f'    </div>'
                )
            else:
                parts = []
                for idx, blk in enumerate(content.get("blocks", [])):
                    badge = blk.get("badge")
                    color = blk.get("color", "b-trans")
                    if badge:
                        style = ' style="margin-top:6px;"' if idx > 0 else ""
                        parts.append(f'<span class="badge {color}"{style}>{html.escape(badge)}</span>')
                    lis = "\n        ".join(f"<li>{format_bullet_text(t)}</li>" for t in blk.get("bullets", []))
                    parts.append(f"<ul>\n        {lis}\n      </ul>")
                if content.get("note"):
                    parts.append(
                        f'<div style="font-size:10.5px;margin-top:6px;color:#854d0e;font-style:italic;">'
                        f'{html.escape(content["note"])}</div>'
                    )
                inner_html = "\n      ".join(parts)
                sg_lines.append(
                    f'    <div class="cell {bg_cls}" data-family="{fid}">\n'
                    f'      <div class="mobile-fam-title">{fam_name}</div>\n'
                    f'      {inner_html}\n'
                    f'    </div>'
                )
    sg_lines.append("  </div>")

    # Build Action Items Grid
    pg_lines = [
        '  <!-- ==================== BOTTOM PORTION ==================== -->',
        '  <div id="action-items" class="bottom-section">',
        '    <div class="section-banner">',
        '      <span>Action Items</span>',
        '      <span class="sub">Action items, shopping lists, and bring checklists per family</span>',
        '    </div>',
        '',
        '    <div class="pre-grid">',
    ]
    for fam in families:
        fid = str(fam["id"])
        bg_cls = fam["header_class"].replace("h-", "bg-")
        sections = action_items.get(fid, [])
        sec_parts = []
        for sec in sections:
            sec_parts.append(f"        <h3>{html.escape(sec['title'])}</h3>")
            sec_parts.append(render_items(sec.get("items", []), indent=8))
        inner = "\n".join(sec_parts)
        pg_lines.append(f'      <div class="pre-col {bg_cls}" data-family="{fid}">\n{inner}\n      </div>')

    pg_lines.append("    </div>")
    pg_lines.append("  </div>")
    pg_lines.append("")

    new_html = (
        head_prefix
        + "\n".join(filter_lines)
        + "\n"
        + top_banner
        + "\n".join(sg_lines)
        + "\n\n"
        + "\n".join(pg_lines)
        + "\n"
        + script_suffix
    )
    OUT_PATH.write_text(new_html, encoding="utf-8")
    print(f"Generated {OUT_PATH.name} from {YAML_PATH.name} ({len(families)} families, {len(schedule)} slots).")


if __name__ == "__main__":
    build()
