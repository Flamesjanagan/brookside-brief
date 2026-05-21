"""
update_macro.py — Daily Macro Terminal updater for The Brookside Brief
Runs via GitHub Actions at 8:30 AM ET on weekdays.

Fetches live market data (yfinance, no API key needed) then calls Claude
to write the Macro Terminal analysis in the site's HTML format.
"""

import os, re, json
from datetime import datetime, date
import pytz
import yfinance as yf
import anthropic

# ── Market symbols ────────────────────────────────────────────────────────────
SYMBOLS = {
    "sp500":     ("^GSPC",    "S&P 500"),
    "nasdaq":    ("^IXIC",    "Nasdaq Composite"),
    "dow":       ("^DJI",     "Dow Jones Industrial Avg."),
    "russell":   ("^RUT",     "Russell 2000"),
    "vix":       ("^VIX",     "VIX"),
    "ust2y":     ("^IRX",     "UST 2-Year"),
    "ust10y":    ("^TNX",     "UST 10-Year"),
    "ust30y":    ("^TYX",     "UST 30-Year"),
    "dxy":       ("DX-Y.NYB", "Dollar Index (DXY)"),
    "eurusd":    ("EURUSD=X", "EUR/USD"),
    "usdjpy":    ("JPY=X",    "USD/JPY"),
    "wti":       ("CL=F",     "WTI Crude"),
    "brent":     ("BZ=F",     "Brent Crude"),
    "gold":      ("GC=F",     "Gold (spot)"),
    "bitcoin":   ("BTC-USD",  "Bitcoin"),
}


def fetch_market_data() -> dict:
    """Pull previous close and change for each symbol via yfinance."""
    results = {}
    for key, (symbol, label) in SYMBOLS.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if len(hist) >= 2:
                prev  = float(hist["Close"].iloc[-2])
                last  = float(hist["Close"].iloc[-1])
                chg   = last - prev
                pct   = (chg / prev) * 100
                results[key] = {
                    "label": label,
                    "symbol": symbol,
                    "price": round(last, 4),
                    "prev_close": round(prev, 4),
                    "change": round(chg, 4),
                    "pct_change": round(pct, 3),
                }
        except Exception as e:
            print(f"  Warning: could not fetch {symbol}: {e}")
    return results


def fmt_price(key: str, data: dict) -> str:
    """Format a price for display (handles rates, FX, equities, crypto)."""
    p = data[key]["price"]
    rate_keys = {"ust2y", "ust10y", "ust30y"}
    if key in rate_keys:
        return f"{p:.2f}%"
    if key == "eurusd":
        return f"{p:.4f}"
    if key == "usdjpy":
        return f"{p:.2f}"
    if key == "bitcoin":
        return f"${p:,.0f}"
    if key in {"wti", "brent", "gold"}:
        return f"${p:,.2f}"
    if key == "dxy":
        return f"{p:.2f}"
    if key == "vix":
        return f"{p:.1f}"
    return f"{p:,.2f}"


def build_prompt(data: dict, today_str: str) -> str:
    lines = []
    for key, d in data.items():
        arrow = "▲" if d["pct_change"] >= 0 else "▼"
        lines.append(
            f"  {d['label']}: {fmt_price(key, data)} "
            f"({arrow} {abs(d['pct_change']):.2f}% / {d['change']:+.4g})"
        )
    data_block = "\n".join(lines)

    return f"""You are the financial editor of The Brookside Brief, a sharp, opinionated daily market publication.

TODAY: {today_str}

LIVE MARKET DATA (previous close):
{data_block}

Write the Macro Terminal section for today's site. It must be 5 HTML tab panels using EXACTLY this structure. Do not add any explanation, markdown, or wrapper tags — output only the 5 divs.

─── CSS classes ───
Positive moves → class="cchg up" and use ▲
Negative moves → class="cchg dn" and use ▼
The "up" and "dn" classes control colour (black vs red).

─── Required output (5 divs) ───

<div class="term-panel active" id="tab-overview">
  <div class="ai-answer">
    <span class="label">The one-line read</span>
    [One punchy sentence — the single dominant market story today. Specific, not generic.]
  </div>
  <div class="cards">
    [6 cards: S&P 500, Nasdaq, Dow, VIX, one rate or commodity most relevant today, Bitcoin]
    Each card:
    <div class="card"><div class="clabel">LABEL</div><div class="cval">VALUE</div><div class="cchg up|dn">▲|▼ X.XX% (±N.NN)</div><div class="cnote">One-line context.</div></div>
  </div>
  <div class="term-narr">
    <p>[2–3 sentences of sharp analytical narrative on the dominant theme]</p>
  </div>
</div>

<div class="term-panel" id="tab-rates">
  <div class="ai-answer">
    <span class="label">Rates read</span>
    [One sentence on the yield curve / rate outlook]
  </div>
  <div class="cards">
    [6 cards: UST 2Y, 10Y, 30Y, 2s10s spread (calculate it), 2s30s spread (calculate it), DXY]
    For spread cards: cval is the spread in bps (10Y minus 2Y, 30Y minus 2Y), cchg shows direction vs prior week.
  </div>
  <div class="term-narr">
    <h4>What to watch</h4>
    <p>[Rate-market narrative — upcoming auctions, Fed speakers, curve shape implications]</p>
  </div>
</div>

<div class="term-panel" id="tab-inflation">
  <div class="ai-answer">
    <span class="label">Inflation read</span>
    [One sentence on inflation backdrop]
  </div>
  <div class="cards">
    [4 cards using the most relevant current data: recent CPI, recent PPI, oil (as inflation proxy), one forward indicator]
  </div>
  <div class="term-narr">
    <h4>The mechanism</h4>
    <p>[How today's data fits the inflation narrative]</p>
  </div>
</div>

<div class="term-panel" id="tab-growth">
  <div class="ai-answer">
    <span class="label">Growth read</span>
    [One sentence on growth momentum]
  </div>
  <div class="cards">
    [6 cards: mix of equity indices as growth proxies, Russell 2000, recent earnings data, one international index]
  </div>
  <div class="term-narr">
    <h4>The pivot point</h4>
    <p>[What data or event would change the growth narrative]</p>
  </div>
</div>

<div class="term-panel" id="tab-risk">
  <div class="ai-answer">
    <span class="label">Risk read</span>
    [One sentence on risk appetite / tail risks]
  </div>
  <div class="cards">
    [5 cards: VIX, Gold, Bitcoin, one credit/spread proxy, one geopolitical risk factor]
  </div>
  <div class="term-narr">
    <h4>The asymmetry</h4>
    <p>[Where the risk is skewed — what breaks first if conditions worsen]</p>
  </div>
</div>

Write like a confident Wall Street analyst. Use the real numbers from the data above. Be specific. Do not hedge with "may" or "could" — make a call."""


def clean_html_output(raw: str) -> str:
    """Strip code fences and any prose Claude adds around the HTML."""
    text = raw.strip()
    # Remove opening code fence (```html or ```)
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    # Remove closing code fence
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    # If Claude added explanation before the first <div, trim it
    first_div = text.find('<div class="term-panel')
    if first_div > 0:
        text = text[first_div:]
    # If Claude added explanation after the last </div>, trim it
    last_div = text.rfind("</div>")
    if last_div != -1:
        text = text[:last_div + 6]
    return text.strip()


def generate_macro_html(data: dict, today_str: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = build_prompt(data, today_str)

    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=(
            "You are a financial editor. Output ONLY raw HTML div elements — "
            "absolutely no markdown, no code fences, no explanation text before or after. "
            "Start your response with '<div' and end it with '</div>'."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text
    cleaned = clean_html_output(raw)

    # Safety check — if we don't have valid-looking output, raise so the
    # workflow fails loudly rather than silently corrupting the page.
    if not cleaned.startswith("<div"):
        raise ValueError(f"Claude returned unexpected output (first 200 chars): {cleaned[:200]}")

    return cleaned


def update_html(new_macro_html: str, today_str: str, today_long: str) -> bool:
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Replace macro tab panels
    pattern = r"<!-- MACRO-AUTO-START -->.*?<!-- MACRO-AUTO-END -->"
    replacement = (
        "<!-- MACRO-AUTO-START -->\n"
        + new_macro_html
        + "\n    <!-- MACRO-AUTO-END -->"
    )
    new_content, n = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if n == 0:
        print("ERROR: MACRO-AUTO-START/END markers not found in index.html")
        return False

    # Update dateline in utility bar
    new_content = re.sub(
        r'(<span id="dateline">)[^<]*(</span>)',
        rf"\g<1>{today_long}\g<2>",
        new_content,
    )

    # Update the macro section sub-header date
    new_content = re.sub(
        r"(synced to today's brief, )[^<.]+(\.\s*</p>)",
        rf"\g<1>{today_str}.\g<2>",
        new_content,
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def main():
    et = pytz.timezone("US/Eastern")
    now = datetime.now(et)
    today_str  = now.strftime("%B %d, %Y")          # "May 21, 2026"
    today_long = now.strftime("%A, %B %d, %Y")      # "Thursday, May 21, 2026"

    print(f"=== Brookside Brief daily update — {today_str} ===")

    print("Fetching market data...")
    data = fetch_market_data()
    print(f"  Got data for {len(data)} instruments.")
    if len(data) < 8:
        raise RuntimeError("Too few instruments fetched — aborting to avoid bad update.")

    print("Calling Claude to generate macro narrative...")
    macro_html = generate_macro_html(data, today_str)
    print(f"  Received {len(macro_html)} chars of HTML.")

    print("Updating index.html...")
    if update_html(macro_html, today_str, today_long):
        print(f"  Done — site updated for {today_str}.")
    else:
        raise RuntimeError("HTML update failed.")


if __name__ == "__main__":
    main()
