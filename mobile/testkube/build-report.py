#!/usr/bin/env python3
"""Build a one-page HTML report for an Android Maestro run.

Inputs, all written by earlier workflow steps under the reports folder:
  device.env   facts about the emulator and the app (key=value lines)
  junit.xml    the Maestro JUnit report
  maestro/     the Maestro test output, with screenshots per flow

Output:
  mobile-report.html, with every screenshot embedded so the page opens
  on its own from the Testkube artifacts list.
"""
import base64
import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPORTS = Path(sys.argv[1] if len(sys.argv) > 1 else "/data/reports")
OUTPUT = REPORTS / "mobile-report.html"


def read_device_facts(path):
    facts = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                facts[key.strip()] = value.strip()
    return facts


def read_flows(junit_path):
    """Return one dict per Maestro flow from the JUnit report."""
    flows = []
    if not junit_path.exists():
        return flows
    root = ET.parse(junit_path).getroot()
    for case in root.iter("testcase"):
        failure = case.find("failure")
        if failure is None:
            failure = case.find("error")
        flows.append({
            "name": case.get("name", "Unnamed flow"),
            "file": case.get("file", ""),
            "seconds": float(case.get("time", "0") or 0),
            "passed": failure is None,
            "message": (failure.get("message") or failure.text or "").strip() if failure is not None else "",
        })
    # Show flows in file order (01-..., 02-...), not in the order Maestro ran them.
    return sorted(flows, key=lambda f: f["file"])


def flow_folder(name):
    """Maestro writes each flow's output to maestro/<run timestamp>/<flow name>/."""
    matches = sorted((REPORTS / "maestro").glob(f"*/{name}"))
    return matches[-1] if matches else None


def screenshots_for(folder):
    if folder is None:
        return []
    return sorted(folder.rglob("*.png"), key=lambda p: p.stat().st_mtime)


def recordings_for(folder):
    if folder is None:
        return []
    return sorted(folder.rglob("*.mp4"))


def embed_png(path):
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def esc(value):
    return html.escape(str(value))


def device_rows(facts):
    rows = [
        ("Device", f"{facts.get('manufacturer', '')} {facts.get('model', '')}".strip() or "Unknown"),
        ("Android", f"Android {facts.get('android', '?')} (API {facts.get('sdk', '?')})"),
        ("CPU", facts.get("abi", "Unknown")),
        ("Screen", f"{facts.get('screen', '?')} pixels, {facts.get('density', '?')} dpi"),
        ("App", f"{facts.get('app_id', '?')} version {facts.get('app_version', '?')}"),
        ("APK source", facts.get("apk_url", "Unknown")),
        ("Emulator address", facts.get("address", "Unknown")),
    ]
    return "\n".join(
        f"<tr><th>{esc(label)}</th><td>{esc(value)}</td></tr>" for label, value in rows
    )


def flow_card(flow):
    folder = flow_folder(flow["name"])
    shots = screenshots_for(folder)
    videos = recordings_for(folder)
    status = "Passed" if flow["passed"] else "Failed"
    status_class = "pass" if flow["passed"] else "fail"

    if shots:
        shot_html = "\n".join(
            f'<figure class="phone"><img src="{embed_png(p)}" alt="{esc(p.stem)}">'
            f"<figcaption>{esc(p.stem)}</figcaption></figure>"
            for p in shots
        )
    else:
        shot_html = '<p class="muted">No screenshots were saved for this flow.</p>'

    message = f'<p class="error">{esc(flow["message"])}</p>' if flow["message"] else ""
    video_html = ""
    if videos:
        names = ", ".join(esc(v.name) for v in videos)
        video_html = f'<p class="muted">Screen recording saved as an artifact: {names}</p>'

    return f"""
    <section class="flow">
      <div class="flow-head">
        <h2>{esc(flow["name"])}</h2>
        <span class="badge {status_class}">{status}</span>
      </div>
      <p class="muted">{esc(flow["file"])} &middot; {flow["seconds"]:.0f} seconds</p>
      {message}
      <div class="shots">{shot_html}</div>
      {video_html}
    </section>"""


def build():
    facts = read_device_facts(REPORTS / "device.env")
    flows = read_flows(REPORTS / "junit.xml")
    passed = sum(1 for f in flows if f["passed"])
    total_seconds = sum(f["seconds"] for f in flows)
    overall = "pass" if flows and passed == len(flows) else "fail"
    title = f"Android {facts.get('android', '')} smoke run".replace("  ", " ")

    cards = "\n".join(flow_card(f) for f in flows) or '<p class="muted">No flow results were found.</p>'

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
  :root {{
    --ink: #1a1d23; --muted: #5f6673; --line: #e3e6eb;
    --pass: #137a3f; --pass-bg: #e6f4ec; --fail: #b42318; --fail-bg: #fdecea;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #ffffff; color: var(--ink);
         font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 1240px; margin: 0 auto; padding: 32px 24px 48px; }}
  header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 24px;
           border-bottom: 1px solid var(--line); padding-bottom: 20px; margin-bottom: 24px; }}
  h1 {{ font-size: 26px; margin: 0 0 4px; }}
  h2 {{ font-size: 18px; margin: 0; }}
  .muted {{ color: var(--muted); margin: 4px 0; }}
  .error {{ color: var(--fail); background: var(--fail-bg); padding: 8px 12px; border-radius: 6px; }}
  .badge {{ font-weight: 600; font-size: 13px; padding: 4px 12px; border-radius: 999px; white-space: nowrap; }}
  .badge.pass {{ color: var(--pass); background: var(--pass-bg); }}
  .badge.fail {{ color: var(--fail); background: var(--fail-bg); }}
  .summary {{ font-size: 16px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 28px; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ width: 180px; color: var(--muted); font-weight: 500; }}
  td {{ word-break: break-all; }}
  .flows {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(560px, 1fr)); gap: 20px; }}
  .flow {{ border: 1px solid var(--line); border-radius: 10px; padding: 20px; }}
  .flow-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
  .shots {{ display: flex; flex-wrap: wrap; gap: 24px; margin-top: 16px; }}
  .phone {{ margin: 0; width: 230px; }}
  .phone img {{ width: 100%; display: block; border: 9px solid #111; border-radius: 26px; background: #000; }}
  .phone figcaption {{ text-align: center; color: var(--muted); font-size: 13px; margin-top: 6px; }}
</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>{esc(title)}</h1>
      <p class="muted">Maestro flows on an Android emulator, run by Testkube inside Kubernetes.</p>
    </div>
    <div class="summary"><span class="badge {overall}">{passed} of {len(flows)} flows passed</span>
      <p class="muted">{total_seconds:.0f} seconds of flow time</p></div>
  </header>
  <table>
    {device_rows(facts)}
  </table>
  <div class="flows">{cards}</div>
</main>
</body>
</html>
"""
    OUTPUT.write_text(page)
    print(f"Wrote {OUTPUT} with {len(flows)} flows ({passed} passed)")


if __name__ == "__main__":
    build()
