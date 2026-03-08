import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timezone
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Backtest Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    background-color: #080c14;
    color: #e2e8f0;
    font-family: 'Syne', sans-serif;
}
section[data-testid="stSidebar"] {
    background-color: #0d1421 !important;
    border-right: 1px solid #1e2d4a;
}
.stButton > button {
    background: linear-gradient(135deg, #00d4ff, #7c3aed);
    color: white; border: none; border-radius: 8px;
    font-family: 'Syne', sans-serif; font-weight: 700;
    padding: 10px 20px; width: 100%;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; color: white; }
.stSelectbox > div > div {
    background-color: #0d1421 !important;
    border: 1px solid #1e2d4a !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stSlider > div > div { color: #00d4ff; }
div[data-testid="metric-container"] {
    background: #0d1421;
    border: 1px solid #1e2d4a;
    border-radius: 10px;
    padding: 16px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #4a6080;
}
.stTabs [aria-selected="true"] {
    color: #00d4ff !important;
    border-bottom-color: #00d4ff !important;
}
.stDataFrame { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }
hr { border-color: #1e2d4a; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────
def get_deepseek_key():
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        return os.environ.get("DEEPSEEK_API_KEY", "")

def load_pro_codes():
    try:
        raw = st.secrets.get("PRO_CODES", "")
        if raw:
            return [c.strip().upper() for c in raw.split(",") if c.strip()]
    except Exception:
        pass
    return []

def check_code(code: str) -> str:
    """Returns 'pro', 'standard', or '' """
    code = code.strip().upper()
    pro_codes = load_pro_codes()
    if code in pro_codes:
        return "pro"
    return ""

# ── Language ──────────────────────────────────────────────────
TEXTS = {
    "en": {
        "title": "📊 Backtest Visualizer",
        "subtitle": "Describe your strategy in plain English — AI converts it to logic and backtests it live.",
        "lang_btn": "🇰🇷 한국어",
        "plan_section": "🔑 Plan",
        "free_plan": "FREE",
        "std_plan": "💎 STANDARD",
        "pro_plan": "🚀 PRO",
        "runs_left": "runs left this session",
        "settings": "⚙️ Settings",
        "indicator": "Indicator",
        "symbol": "Symbol",
        "timeframe": "Timeframe",
        "candles": "Candles",
        "strategy_section": "📝 Strategy",
        "strategy_label": "Describe your strategy",
        "strategy_placeholder": "Example:\nBuy when MACD line crosses above signal line.\nSell when MACD line crosses below signal line.\nStop loss: 1.5%",
        "strategy_guide": "💡 Guide",
        "guide_content": """**How to write a strategy:**
- Entry condition (e.g. "Buy when RSI drops below 30")
- Exit condition (e.g. "Sell when RSI rises above 70")
- Optional: Stop loss %, Take profit %
- Optional: Trend filter (e.g. "Only buy above 200 EMA")
- Optional: Stoch RSI filter (e.g. "Only enter when Stoch RSI between 0.2 and 0.8")
- Optional: Trailing stop (e.g. "Trailing stop arms at 0.5%, gap 0.3%")
- Optional: Max hold time (e.g. "Close after 3 hours")

**MACD — Basic:**
Buy when MACD crosses above signal. Sell when MACD crosses below signal. Stop loss 1.5%.

**MACD — With filters (Jin bot style):**
Buy when MACD crosses above signal AND histogram > 5 AND MACD slope > 0.3, Stoch RSI between 0.2 and 0.8. Trailing stop arms at 0.5%, gap 0.3%. Max hold 3 hours. Stop loss 1.5%.

**MACD — With histogram direction filter:**
Buy when MACD crosses above signal AND histogram is increasing. Sell when MACD crosses below signal. Stop loss 1.5%.

**RSI example:**
Buy when RSI < 30. Sell when RSI > 70. Stop loss 2%. Take profit 4%.

**BB example:**
Buy when price touches lower Bollinger Band. Sell at middle band. Stop loss 1%.

**With trailing stop:**
Buy when MACD crosses above signal. Sell on MACD cross. Trailing stop arms at 0.3%, gap 0.25%. Stop loss 1.5%.
""",
        "run_btn": "▶ RUN BACKTEST",
        "enter_code": "🔑 Enter Subscription Code",
        "apply_code": "Apply",
        "code_ok": "🚀 Pro plan activated!",
        "code_fail": "❌ Invalid code",
        "how_sub": "🛒 How to Subscribe",
        "sub_steps": ["1. Choose plan → pay via Gumroad", "2. Check email for code", "3. Enter code above"],
        "buy_pro": "🚀 Buy Pro — $9/mo",
        "tab_result": "Result",
        "tab_trades": "Trade Log",
        "tab_ai": "AI Analysis",
        "total_pnl": "Total PnL",
        "winrate": "Win Rate",
        "avg_hold": "Avg Hold",
        "max_loss": "Max Loss",
        "consec_loss": "Max Consec. Loss",
        "trades_count": "Trades",
        "price_chart": "Price Chart — Entry / Exit Points",
        "equity_chart": "Equity Curve",
        "trade_log": "Trade Log",
        "ai_btn": "🤖 Analyze with AI",
        "ai_loading": "Analyzing your strategy...",
        "ai_pro_only": "🔑 AI Analysis requires Pro plan",
        "no_runs": "⚠️ No runs left. Upgrade to Pro for unlimited backtests.",
        "fetching": "Fetching data from Binance...",
        "running": "Running backtest...",
        "free_limit_tf": "⚠️ Free plan: 1H timeframe only",
        "free_limit_candles": "⚠️ Free plan: max 30 candles",
        "minutes": "min",
        "legend_entry": "Entry",
        "legend_exit_win": "Exit (Win)",
        "legend_exit_loss": "Exit (Loss)",
        "col_open": "Open Time",
        "col_close": "Close Time",
        "col_side": "Side",
        "col_entry": "Entry",
        "col_exit": "Exit",
        "col_pnl": "PnL (USDT)",
        "col_hold": "Hold (min)",
        "col_result": "Result",
    },
    "ko": {
        "title": "📊 백테스트 시각화",
        "subtitle": "전략을 글로 설명하면 AI가 로직으로 변환해서 바로 백테스팅합니다.",
        "lang_btn": "🇺🇸 English",
        "plan_section": "🔑 플랜",
        "free_plan": "무료",
        "std_plan": "💎 스탠다드",
        "pro_plan": "🚀 프로",
        "runs_left": "회 남음",
        "settings": "⚙️ 설정",
        "indicator": "지표",
        "symbol": "심볼",
        "timeframe": "타임프레임",
        "candles": "봉 개수",
        "strategy_section": "📝 전략",
        "strategy_label": "전략을 글로 설명하세요",
        "strategy_placeholder": "예시:\nMACD 라인이 시그널 라인을 상향 돌파하면 매수.\nMACD 라인이 시그널 라인을 하향 돌파하면 매도.\n손절: 1.5%",
        "strategy_guide": "💡 작성 가이드",
        "guide_content": """**전략 작성 방법:**
- 진입 조건 (예: "RSI가 30 아래로 내려가면 매수")
- 청산 조건 (예: "RSI가 70 위로 올라가면 매도")
- 선택: 손절 %, 익절 %
- 선택: 추세 필터 (예: "200 EMA 위에서만 매수")
- 선택: Stoch RSI 필터 (예: "Stoch RSI 0.2~0.8 구간에서만 진입")
- 선택: 트레일링 스탑 (예: "트레일링 스탑 0.5% 발동, 간격 0.3%")
- 선택: 최대 보유 시간 (예: "3시간 후 강제 청산")

**MACD — 기본:**
MACD가 시그널을 상향 돌파하면 매수. 하향 돌파하면 매도. 손절 1.5%.

**MACD — 복합 필터 (Jin 봇 스타일):**
MACD 상향 돌파하고 히스토그램 5 초과, MACD 기울기 0.3 초과, Stoch RSI 0.2~0.8 구간. 트레일링 스탑 0.5% 발동, 간격 0.3%. 최대 보유 3시간. 손절 1.5%.

**MACD — 히스토그램 방향 필터:**
MACD 상향 돌파하고 히스토그램 상승 중(histogram turning up). 하향 돌파하면 매도. 손절 1.5%.

**RSI 예시:**
RSI 30 미만이면 매수. RSI 70 초과이면 매도. 손절 2%. 익절 4%.

**볼린저 밴드 예시:**
가격이 하단 밴드에 터치하면 매수. 중간 밴드에서 매도. 손절 1%.

**트레일링 스탑 예시:**
MACD 상향 돌파하면 매수. 하향 돌파하면 매도. 트레일링 스탑 0.3% 발동, 간격 0.25%. 손절 1.5%.
""",
        "run_btn": "▶ 백테스트 실행",
        "enter_code": "🔑 구독 코드 입력",
        "apply_code": "적용",
        "code_ok": "🚀 Pro 플랜 활성화!",
        "code_fail": "❌ 잘못된 코드",
        "how_sub": "🛒 구독 방법",
        "sub_steps": ["1. 플랜 선택 → Gumroad 결제", "2. 이메일로 코드 수신", "3. 위에 코드 입력"],
        "buy_pro": "🚀 Pro 구매 — $9/월",
        "tab_result": "결과",
        "tab_trades": "거래 내역",
        "tab_ai": "AI 분석",
        "total_pnl": "총 PnL",
        "winrate": "승률",
        "avg_hold": "평균 보유",
        "max_loss": "최대 손실",
        "consec_loss": "최대 연속 손실",
        "trades_count": "거래 횟수",
        "price_chart": "가격 차트 — 진입 / 청산 포인트",
        "equity_chart": "에쿼티 커브",
        "trade_log": "거래 내역",
        "ai_btn": "🤖 AI 분석 실행",
        "ai_loading": "전략 분석 중...",
        "ai_pro_only": "🔑 AI 분석은 Pro 플랜 전용입니다",
        "no_runs": "⚠️ 실행 횟수가 소진되었습니다. Pro로 업그레이드하면 무제한 사용 가능합니다.",
        "fetching": "바이낸스에서 데이터 수신 중...",
        "running": "백테스트 실행 중...",
        "free_limit_tf": "⚠️ 무료 플랜: 1시간봉 고정",
        "free_limit_candles": "⚠️ 무료 플랜: 최대 30봉",
        "minutes": "분",
        "legend_entry": "진입",
        "legend_exit_win": "청산(수익)",
        "legend_exit_loss": "청산(손실)",
        "col_open": "진입 시간",
        "col_close": "청산 시간",
        "col_side": "방향",
        "col_entry": "진입가",
        "col_exit": "청산가",
        "col_pnl": "PnL (USDT)",
        "col_hold": "보유(분)",
        "col_result": "결과",
    }
}

# ── Session state ─────────────────────────────────────────────
if "lang"      not in st.session_state: st.session_state.lang = "en"
if "plan"      not in st.session_state: st.session_state.plan = "free"
if "runs_left" not in st.session_state: st.session_state.runs_left = 3
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "market"    not in st.session_state: st.session_state.market = "spot"

lang = st.session_state.lang
t    = TEXTS[lang]
plan = st.session_state.plan

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:

    # Language toggle
    if st.button(t["lang_btn"]):
        st.session_state.lang = "ko" if lang == "en" else "en"
        st.rerun()

    st.divider()

    # Plan display
    st.markdown(f"### {t['plan_section']}")

    plan_colors = {"free": "#4a6080", "pro": "#7c3aed"}
    plan_labels = {"free": t["free_plan"], "pro": t["pro_plan"]}
    cur_color   = plan_colors.get(plan, "#4a6080")
    cur_label   = plan_labels.get(plan, t["free_plan"])

    st.markdown(
        f'<div style="background:#0d1421;border:1px solid {cur_color};border-radius:8px;'
        f'padding:10px 14px;font-family:JetBrains Mono,monospace;font-size:0.8rem;">'
        f'<b style="color:{cur_color};">{cur_label}</b>'
        + (f'<br><span style="color:#ef4444;font-size:0.7rem;">▶ {st.session_state.runs_left} {t["runs_left"]}</span>'
           if plan == "free" else
           '<br><span style="color:#00ff88;font-size:0.7rem;">✓ Unlimited runs</span>')
        + '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Settings
    st.markdown(f"#### {t['settings']}")

    indicator = st.selectbox(
        t["indicator"],
        ["MACD", "RSI", "Bollinger Bands"],
        disabled=(plan == "free"),  # free는 MACD 고정
        index=0,
    )
    if plan == "free":
        indicator = "MACD"

    symbol_options = (
        ["ETHUSDT", "BTCUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
        if plan == "pro" else ["ETHUSDT"]
    )
    symbol = st.selectbox(t["symbol"], symbol_options)

    tf_options_all = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"1h","4h":"4h"}
    if plan == "free":
        tf = "1h"
        st.markdown(
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#4a6080;">'
            f'{t["timeframe"]}: <b style="color:#00d4ff;">1H</b> (Free fixed)</span>',
            unsafe_allow_html=True,
        )
    else:
        tf = st.selectbox(t["timeframe"], list(tf_options_all.keys()), index=4)

    if plan == "free":
        candles = 30
        st.markdown(
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#4a6080;">'
            f'{t["candles"]}: <b style="color:#00d4ff;">30</b> (Free fixed)</span>',
            unsafe_allow_html=True,
        )
    else:
        candles = st.slider(t["candles"], min_value=30, max_value=200, value=100, step=10)

    st.session_state.market = "spot"

    st.divider()

    # Code input
    st.markdown(f"#### {t['enter_code']}")
    code_input = st.text_input("", placeholder="BT-XXXX-XXXX", type="password", label_visibility="collapsed")
    if st.button(t["apply_code"]):
        result = check_code(code_input)
        if result == "pro":
            st.session_state.plan = "pro"
            st.success(t["code_ok"])
            st.rerun()
        else:
            st.error(t["code_fail"])

    st.divider()

    st.markdown(f"#### {t['how_sub']}")
    for step in t["sub_steps"]:
        st.markdown(
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#4a6080;">{step}</span>',
            unsafe_allow_html=True,
        )
    GUMROAD = "https://sparkle488.gumroad.com"
    st.markdown(
        f'<br><a href="{GUMROAD}" target="_blank">'
        f'<div style="background:linear-gradient(135deg,#7c3aed,#00d4ff);color:#fff;'
        f'text-align:center;padding:8px;border-radius:8px;font-size:0.8rem;'
        f'font-weight:700;cursor:pointer;">{t["buy_pro"]}</div></a>',
        unsafe_allow_html=True,
    )

# ── Main ──────────────────────────────────────────────────────
st.markdown(f"## {t['title']}")
st.markdown(f'<p style="color:#4a6080;font-family:JetBrains Mono,monospace;font-size:0.8rem;">{t["subtitle"]}</p>', unsafe_allow_html=True)

disclaimer = (
    "⚠️ **Disclaimer**: This tool is for educational and informational purposes only. "
    "Backtest results are based on historical data and do not guarantee future performance. "
    "This is not financial advice. All trading decisions are solely your responsibility."
    if lang == "en" else
    "⚠️ **면책 공고**: 본 툴은 교육 및 정보 제공 목적으로만 제공됩니다. "
    "백테스트 결과는 과거 데이터 기반이며 미래 수익을 보장하지 않습니다. "
    "본 툴은 투자 권유가 아니며, 모든 투자 결정의 책임은 사용자 본인에게 있습니다."
)
st.markdown(
    f'<div style="background:#1a0d00;border:1px solid #92400e;border-radius:8px;'
    f'padding:10px 14px;font-family:JetBrains Mono,monospace;font-size:0.72rem;'
    f'color:#d97706;line-height:1.6;">{disclaimer}</div>',
    unsafe_allow_html=True,
)
st.divider()

# ── Strategy input (메인 화면) ────────────────────────────────
st.markdown(f"### {t['strategy_section']}")

with st.expander(t["strategy_guide"], expanded=False):
    st.markdown(t["guide_content"])

st.markdown(
    '<div style="border:2px solid #1e2d4a;border-radius:10px;padding:4px 8px;'
    'background:#0d1421;margin-bottom:4px;">'
    '<span style="font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#4a6080;">'
    '✏️ ' + ("Write your strategy below" if "en" in str(st.session_state.lang) else "전략을 아래에 입력하세요") +
    '</span></div>',
    unsafe_allow_html=True,
)

max_chars = 100 if plan == "free" else 500

strategy_text = st.text_area(
    label="strategy_input",
    placeholder=TEXTS[st.session_state.lang]["strategy_placeholder"],
    height=130,
    label_visibility="collapsed",
    key="strategy_input_main",
    max_chars=max_chars,
)

# 글자수 카운터
cur_len = len(strategy_text)
char_color = "#ef4444" if cur_len >= max_chars else "#4a6080"
st.markdown(
    f'<div style="text-align:right;font-family:JetBrains Mono,monospace;'
    f'font-size:0.7rem;color:{char_color};">'
    f'{cur_len} / {max_chars}'
    + (" — <b>Upgrade to Pro for 500 chars</b>" if plan == "free" and cur_len >= 90 else "")
    + '</div>',
    unsafe_allow_html=True,
)

# 초기자본 + 수수료
col_eq, col_fee = st.columns(2)
with col_eq:
    initial_equity = st.number_input(
        "💰 " + ("Initial Capital (USDT)" if lang == "en" else "초기 자본 (USDT)"),
        min_value=10.0, max_value=100000.0, value=1000.0, step=100.0,
        format="%.1f",
    )
with col_fee:
    fee_pct = st.number_input(
        "💸 " + ("Fee per trade (%)" if lang == "en" else "거래 수수료 (%)"),
        min_value=0.0, max_value=1.0, value=0.04, step=0.01,
        format="%.3f",
        help="Binance Futures taker fee: 0.04% / Spot: 0.1%",
    )

# RUN 버튼 — 크고 명확하게
st.markdown("<br>", unsafe_allow_html=True)
run_clicked = st.button(
    label=TEXTS[st.session_state.lang]["run_btn"],
    use_container_width=True,
    type="primary",
)
st.divider()

# ── Backtest engine ───────────────────────────────────────────
SPOT_URL = "https://api.binance.us/api/v3/klines"

def fetch_binance_klines(symbol: str, interval: str, limit: int, market: str = "spot") -> pd.DataFrame:
    url = SPOT_URL
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","qav","trades","tbav","tqav","ignore"
    ])
    for col in ["open","high","low","close","volume"]:
        df[col] = df[col].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df[["open_time","open","high","low","close","volume"]]


def calc_macd(df: pd.DataFrame, fast=12, slow=26, signal=9):
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast).mean()
    df["ema_slow"] = df["close"].ewm(span=slow).mean()
    df["macd"]     = df["ema_fast"] - df["ema_slow"]
    df["signal"]   = df["macd"].ewm(span=signal).mean()
    df["hist"]     = df["macd"] - df["signal"]
    return df


def calc_rsi(df: pd.DataFrame, period=14):
    df = df.copy()
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / (loss + 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def calc_bb(df: pd.DataFrame, period=20, std=2):
    df = df.copy()
    df["bb_mid"]   = df["close"].rolling(period).mean()
    df["bb_std"]   = df["close"].rolling(period).std()
    df["bb_upper"] = df["bb_mid"] + std * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - std * df["bb_std"]
    return df


def calc_stoch_rsi(df: pd.DataFrame, rsi_period=14, stoch_period=14, k_period=3, d_period=3):
    """Stoch RSI(14,14,3,3) — K값 0~1 스케일로 반환 (Jin 봇 srk 컬럼과 동일)"""
    df = df.copy()
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    rs    = gain / (loss + 1e-10)
    rsi   = 100 - (100 / (1 + rs))
    sr_min = rsi.rolling(stoch_period).min()
    sr_max = rsi.rolling(stoch_period).max()
    sr    = (rsi - sr_min) / (sr_max - sr_min + 1e-10)
    df["srk"] = sr.rolling(k_period).mean()   # %K
    df["srd"] = df["srk"].rolling(d_period).mean()  # %D
    return df


def parse_strategy_with_ai(strategy_text: str, indicator: str, lang: str) -> dict:
    """DeepSeek으로 전략 텍스트 → Python 파라미터 변환"""
    api_key = get_deepseek_key()
    if not api_key:
        # fallback: default params
        return {"stop_loss_pct": 1.5, "take_profit_pct": 3.0, "indicator": indicator}

    prompt = f"""You are a trading strategy parser. Extract ALL conditions from the strategy and convert to JSON.

Indicator: {indicator}
Strategy: {strategy_text}

Return ONLY a JSON object with these fields:
- stop_loss_pct: float (default 1.5, e.g. "stop loss 2%" -> 2.0)
- take_profit_pct: float (default 0, e.g. "take profit 3%" -> 3.0, 0=disabled)
- rsi_oversold: float (RSI entry threshold, default 30)
- rsi_overbought: float (RSI exit threshold, default 70)
- use_ema_filter: bool (true if EMA/MA trend filter mentioned, default false)
- ema_period: int (EMA period, default 200)
- macd_hist_min: float (MACD histogram abs minimum for entry, default 0. e.g. "histogram > 10" -> 10.0)
- macd_slope_min: float (MACD line slope minimum for entry, default 0. e.g. "MACD slope > 0.5" or "MACD momentum > 0.3" -> 0.5. slope = current MACD - previous MACD)
- macd_hist_slope: bool (true if entry requires histogram slope turning positive, default false. e.g. "histogram increasing" or "histogram turning up")
- bb_exit_at_mid: bool (BB exit at middle band=true, upper band=false, default true)
- stoch_rsi_min: float (Stoch RSI K min for entry, 0~1 scale, default 0. e.g. "Stoch RSI above 0.3" -> 0.3, "oversold stoch" -> 0.2)
- stoch_rsi_max: float (Stoch RSI K max for entry, 0~1 scale, default 1. e.g. "Stoch RSI below 0.8" -> 0.8, "overbought block" -> 0.8)
- trail_arm_pct: float (trailing stop arm threshold %, default 0=disabled. e.g. "trailing stop arms at 0.3%" -> 0.3)
- trail_gap_pct: float (trailing stop gap %, default 0.25. e.g. "trailing gap 0.5%" -> 0.5)
- max_hold_min: int (max holding time in minutes, default 0=disabled. e.g. "close after 3 hours" -> 180, "max hold 2h" -> 120)

Examples:
- "MACD crosses above signal AND histogram absolute value > 10, stop loss 1.5%" -> {{"stop_loss_pct":1.5,"macd_hist_min":10.0,"macd_slope_min":0,"use_ema_filter":false,"ema_period":200,"take_profit_pct":0}}
- "MACD crosses above signal, slope > 0.5, histogram > 5, stop loss 2%" -> {{"stop_loss_pct":2.0,"macd_slope_min":0.5,"macd_hist_min":5.0,"take_profit_pct":0,"use_ema_filter":false}}
- "RSI below 25 buy, above 75 sell, stop loss 2%, take profit 4%" -> {{"stop_loss_pct":2.0,"take_profit_pct":4.0,"rsi_oversold":25,"rsi_overbought":75,"use_ema_filter":false}}
- "Buy at lower BB, sell at middle band, only above 200 EMA" -> {{"stop_loss_pct":1.5,"take_profit_pct":0,"bb_exit_at_mid":true,"use_ema_filter":true,"ema_period":200}}
- "MACD cross, Stoch RSI above 0.3, trailing stop arm 0.5%, gap 0.3%, max hold 3h" -> {{"stop_loss_pct":1.5,"macd_hist_min":0,"stoch_rsi_min":0.3,"stoch_rsi_max":1,"trail_arm_pct":0.5,"trail_gap_pct":0.3,"max_hold_min":180}}

Return ONLY the JSON, no explanation, no markdown."""


    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 200, "temperature": 0.1},
            timeout=15,
        )
        import json, re
        text = resp.json()["choices"][0]["message"]["content"]
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception:
        return {"stop_loss_pct": 1.5, "take_profit_pct": 3.0,
                "rsi_oversold": 30, "rsi_overbought": 70,
                "use_ema_filter": False, "ema_period": 200}


def run_backtest(df: pd.DataFrame, indicator: str, params: dict,
                 initial_equity=1000.0, fee_pct=0.0004) -> dict:
    df = df.copy().reset_index(drop=True)

    # ── 지표 계산 ──
    if indicator == "MACD":
        df = calc_macd(df)
    elif indicator == "RSI":
        df = calc_rsi(df)
    elif indicator == "Bollinger Bands":
        df = calc_bb(df)

    # A1: Stoch RSI — 항상 계산 (필터 사용 여부와 무관)
    df = calc_stoch_rsi(df)

    # EMA 추세 필터
    if params.get("use_ema_filter"):
        ema_p = int(params.get("ema_period", 200))
        df["ema_filter"] = df["close"].ewm(span=ema_p).mean()

    sl_pct = float(params.get("stop_loss_pct", 1.5)) / 100
    tp_pct = float(params.get("take_profit_pct", 0))  / 100

    # A1: Stoch RSI 진입 필터 파라미터
    srk_min = float(params.get("stoch_rsi_min", 0))    # 0 = 비활성
    srk_max = float(params.get("stoch_rsi_max", 1))    # 1 = 비활성

    # B1: 트레일링 스탑 파라미터 (Jin 봇 TRAIL_PARAMS와 동일 구조)
    trail_arm = float(params.get("trail_arm_pct", 0))  / 100  # 0 = 비활성
    trail_gap = float(params.get("trail_gap_pct", 0.25)) / 100

    # B3: 최대 보유 시간
    max_hold_min = int(params.get("max_hold_min", 0))  # 0 = 비활성

    trades   = []
    equity   = initial_equity
    position = None   # {"entry_price","entry_idx","entry_time","qty","trail_hfp","trail_stop","trail_armed"}
    qty_usdt = equity * 0.1

    for i in range(2, len(df)):
        price = df.loc[i, "close"]
        ts    = df.loc[i, "open_time"]

        # ── Entry ──────────────────────────────────────────────
        if position is None:
            entry_signal = False

            if indicator == "MACD":
                prev_diff  = df.loc[i-1, "macd"] - df.loc[i-1, "signal"]
                curr_diff  = df.loc[i,   "macd"] - df.loc[i,   "signal"]
                hist_abs   = abs(df.loc[i, "hist"]) if "hist" in df.columns else 999
                hist_min   = float(params.get("macd_hist_min", 0))
                macd_slope = df.loc[i, "macd"] - df.loc[i-1, "macd"]
                slope_min  = float(params.get("macd_slope_min", 0))
                hist_slope_ok = True
                if params.get("macd_hist_slope", False):
                    prev_hist = df.loc[i-1, "hist"] if "hist" in df.columns else 0
                    curr_hist = df.loc[i,   "hist"] if "hist" in df.columns else 0
                    hist_slope_ok = (prev_hist < curr_hist)
                entry_signal = (
                    prev_diff < 0 and curr_diff >= 0
                    and hist_abs > hist_min
                    and macd_slope > slope_min
                    and hist_slope_ok
                )

            elif indicator == "RSI":
                rsi_val = df.loc[i, "rsi"] if "rsi" in df.columns else 50
                entry_signal = (rsi_val < float(params.get("rsi_oversold", 30)))

            elif indicator == "Bollinger Bands":
                if "bb_lower" in df.columns:
                    entry_signal = (price <= df.loc[i, "bb_lower"])

            # EMA 추세 필터
            if params.get("use_ema_filter") and "ema_filter" in df.columns:
                entry_signal = entry_signal and (price > df.loc[i, "ema_filter"])

            # A1: Stoch RSI 필터 (srk_min > 0 또는 srk_max < 1 일 때만 적용)
            if entry_signal and (srk_min > 0 or srk_max < 1):
                srk_val = df.loc[i, "srk"] if "srk" in df.columns else 0.5
                if not (srk_min <= srk_val <= srk_max):
                    entry_signal = False

            if entry_signal:
                qty = qty_usdt / price
                position = {
                    "entry_price":  price,
                    "entry_idx":    i,
                    "entry_time":   ts,
                    "qty":          qty,
                    # B1 트레일링 스탑 상태
                    "trail_hfp":    price,   # highest favorable price
                    "trail_stop":   0.0,
                    "trail_armed":  False,
                }

        # ── Exit ───────────────────────────────────────────────
        elif position is not None:
            entry_price = position["entry_price"]
            qty         = position["qty"]
            pct_change  = (price - entry_price) / entry_price
            exit_signal = False
            exit_reason = ""

            # B1: 트레일링 스탑 업데이트 (arm_pct 설정 시만)
            if trail_arm > 0:
                hfp = max(position["trail_hfp"], price)
                position["trail_hfp"] = hfp
                gain_pct = (hfp - entry_price) / entry_price
                if gain_pct >= trail_arm:
                    position["trail_armed"] = True
                if position["trail_armed"]:
                    new_stop = hfp * (1 - trail_gap)
                    if position["trail_stop"] == 0.0 or new_stop > position["trail_stop"]:
                        position["trail_stop"] = new_stop
                if position["trail_armed"] and position["trail_stop"] > 0 and price <= position["trail_stop"]:
                    exit_signal = True
                    exit_reason = "TRAIL"

            # Stop loss (트레일링 미작동 시)
            if not exit_signal and sl_pct > 0 and pct_change <= -sl_pct:
                exit_signal = True
                exit_reason = "SL"

            # Take profit
            if not exit_signal and tp_pct > 0 and pct_change >= tp_pct:
                exit_signal = True
                exit_reason = "TP"

            # B3: 최대 보유 시간 초과
            if not exit_signal and max_hold_min > 0:
                held_min = (ts - position["entry_time"]).total_seconds() / 60
                if held_min >= max_hold_min:
                    exit_signal = True
                    exit_reason = "MAX_HOLD"

            # 지표 청산 신호
            if not exit_signal:
                if indicator == "MACD":
                    prev_diff = df.loc[i-1, "macd"] - df.loc[i-1, "signal"]
                    curr_diff = df.loc[i,   "macd"] - df.loc[i,   "signal"]
                    if prev_diff >= 0 and curr_diff < 0:
                        exit_signal = True
                        exit_reason = "SIGNAL"

                elif indicator == "RSI":
                    rsi_val = df.loc[i, "rsi"] if "rsi" in df.columns else 50
                    if rsi_val > float(params.get("rsi_overbought", 70)):
                        exit_signal = True
                        exit_reason = "SIGNAL"

                elif indicator == "Bollinger Bands":
                    exit_col = "bb_mid" if params.get("bb_exit_at_mid", True) else "bb_upper"
                    if exit_col in df.columns and price >= df.loc[i, exit_col]:
                        exit_signal = True
                        exit_reason = "SIGNAL"

            if exit_signal:
                fee   = (entry_price + price) * qty * fee_pct
                pnl   = (price - entry_price) * qty - fee
                hold  = int((ts - position["entry_time"]).total_seconds() / 60)
                equity += pnl
                trades.append({
                    "open_ts":      position["entry_time"],
                    "close_ts":     ts,
                    "entry":        round(entry_price, 4),
                    "exit":         round(price, 4),
                    "qty":          round(qty, 6),
                    "pnl_usdt":     round(pnl, 4),
                    "fee_usdt":     round(fee, 4),
                    "hold_minutes": hold,
                    "reason":       exit_reason,
                    "entry_idx":    position["entry_idx"],
                    "exit_idx":     i,
                })
                position = None
                qty_usdt = equity * 0.1

    # Force close
    if position is not None:
        last_price = df.iloc[-1]["close"]
        fee  = (position["entry_price"] + last_price) * position["qty"] * fee_pct
        pnl  = (last_price - position["entry_price"]) * position["qty"] - fee
        hold = int((df.iloc[-1]["open_time"] - position["entry_time"]).total_seconds() / 60)
        equity += pnl
        trades.append({
            "open_ts":      position["entry_time"],
            "close_ts":     df.iloc[-1]["open_time"],
            "entry":        round(position["entry_price"], 4),
            "exit":         round(last_price, 4),
            "qty":          round(position["qty"], 6),
            "pnl_usdt":     round(pnl, 4),
            "fee_usdt":     round(fee, 4),
            "hold_minutes": hold,
            "reason":       "CLOSE",
            "entry_idx":    position["entry_idx"],
            "exit_idx":     len(df)-1,
        })

    df_trades = pd.DataFrame(trades) if trades else pd.DataFrame()

    return {
        "df":         df,
        "df_trades":  df_trades,
        "initial_eq": initial_equity,
        "final_eq":   round(equity, 4),
        "indicator":  indicator,
    }



# ── Run backtest ──────────────────────────────────────────────
if run_clicked:
    if plan == "free" and st.session_state.runs_left <= 0:
        st.error(t["no_runs"])
    elif not strategy_text.strip():
        st.warning("Please describe your strategy first." if lang == "en" else "전략을 먼저 입력해주세요.")
    else:
        with st.spinner(t["fetching"]):
            try:
                df_raw = fetch_binance_klines(symbol, tf, candles, market=st.session_state.market)
            except Exception as e:
                st.error(f"Binance API error: {e}")
                st.stop()

        with st.spinner(t["running"]):
            params = parse_strategy_with_ai(strategy_text, indicator, lang)
            result = run_backtest(df_raw, indicator, params,
                                  initial_equity=initial_equity,
                                  fee_pct=fee_pct / 100)

        st.session_state.bt_result = result
        if plan == "free":
            st.session_state.runs_left -= 1
        st.rerun()


# ── Display results ───────────────────────────────────────────
res = st.session_state.bt_result

if res is None:
    st.markdown(
        '<div style="text-align:center;padding:80px;color:#4a6080;'
        'font-family:JetBrains Mono,monospace;font-size:0.85rem;">'
        '← Describe your strategy and click RUN BACKTEST'
        '</div>', unsafe_allow_html=True
    )
    st.stop()

df       = res["df"]
df_tr    = res["df_trades"]
init_eq  = res["initial_eq"]
final_eq = res["final_eq"]
ind      = res["indicator"]

# ── KPI ──────────────────────────────────────────────────────
total_pnl   = round(final_eq - init_eq, 4)
n_trades    = len(df_tr)
wins        = int((df_tr["pnl_usdt"] > 0).sum()) if n_trades > 0 else 0
losses      = n_trades - wins
winrate     = round(wins / n_trades * 100, 1) if n_trades > 0 else 0
avg_hold    = round(df_tr["hold_minutes"].mean(), 0) if n_trades > 0 else 0
max_loss    = round(df_tr["pnl_usdt"].min(), 4) if n_trades > 0 else 0

consec, cur = 0, 0
for _, row in df_tr.iterrows():
    if row["pnl_usdt"] < 0:
        cur += 1; consec = max(consec, cur)
    else:
        cur = 0

pnl_color  = "normal" if total_pnl >= 0 else "inverse"
wr_color   = "normal" if winrate >= 50 else "inverse"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric(t["total_pnl"],    f"{total_pnl:+.4f} U",  delta=f"{(total_pnl/init_eq*100):+.2f}%")
c2.metric(t["winrate"],      f"{winrate}%",           delta=f"{wins}W {losses}L")
c3.metric(t["trades_count"], str(n_trades))
c4.metric(t["avg_hold"],     f"{avg_hold:.0f} {t['minutes']}")
c5.metric(t["max_loss"],     f"{max_loss:.4f} U")
c6.metric(t["consec_loss"],  str(consec))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([t["tab_result"], t["tab_trades"], t["tab_ai"]])

# ════════════════════
# TAB 1 — Charts
# ════════════════════
with tab1:

    COLORS = {
        "price":  "#00d4ff",
        "equity": "#f97316",
        "entry":  "#00ff88",
        "win":    "#00ff88",
        "loss":   "#ff4466",
        "hist_p": "#00ff88",
        "hist_n": "#ff4466",
        "macd":   "#00d4ff",
        "signal": "#f97316",
        "rsi":    "#a78bfa",
        "bb_u":   "#4a6080",
        "bb_l":   "#4a6080",
        "bb_m":   "#94a3b8",
    }

    # ── Price chart with indicator subplot ──
    rows = 2
    row_heights = [0.65, 0.35]
    subplot_titles = [t["price_chart"], ind]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.04,
        subplot_titles=subplot_titles,
    )

    # Price
    fig.add_trace(go.Scatter(
        x=df["open_time"], y=df["close"],
        name="Price", line=dict(color=COLORS["price"], width=1.5),
        hovertemplate="%{x}<br>%{y:.2f}<extra></extra>",
    ), row=1, col=1)

    # Entry/Exit markers
    if n_trades > 0:
        for _, trade in df_tr.iterrows():
            color = COLORS["win"] if trade["pnl_usdt"] >= 0 else COLORS["loss"]
            # Entry
            fig.add_trace(go.Scatter(
                x=[trade["open_ts"]], y=[trade["entry"]],
                mode="markers",
                marker=dict(symbol="triangle-up", color=COLORS["entry"], size=10),
                name=t["legend_entry"], showlegend=False,
                hovertemplate=f"Entry: {trade['entry']}<extra></extra>",
            ), row=1, col=1)
            # Exit
            fig.add_trace(go.Scatter(
                x=[trade["close_ts"]], y=[trade["exit"]],
                mode="markers",
                marker=dict(symbol="triangle-down", color=color, size=10),
                name=t["legend_exit_win"] if trade["pnl_usdt"] >= 0 else t["legend_exit_loss"],
                showlegend=False,
                hovertemplate=f"Exit: {trade['exit']}<br>PnL: {trade['pnl_usdt']:+.4f}<extra></extra>",
            ), row=1, col=1)
            # Shaded region
            fig.add_vrect(
                x0=trade["open_ts"], x1=trade["close_ts"],
                fillcolor=color, opacity=0.05,
                layer="below", line_width=0,
                row=1, col=1,
            )

    # Indicator subplot
    if ind == "MACD" and "macd" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["open_time"], y=df["macd"],
            name="MACD", line=dict(color=COLORS["macd"], width=1.2),
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=df["open_time"], y=df["signal"],
            name="Signal", line=dict(color=COLORS["signal"], width=1.2),
        ), row=2, col=1)
        colors_hist = [COLORS["hist_p"] if v >= 0 else COLORS["hist_n"] for v in df["hist"]]
        fig.add_trace(go.Bar(
            x=df["open_time"], y=df["hist"],
            name="Histogram", marker_color=colors_hist, opacity=0.6,
        ), row=2, col=1)

    elif ind == "RSI" and "rsi" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["open_time"], y=df["rsi"],
            name="RSI", line=dict(color=COLORS["rsi"], width=1.5),
        ), row=2, col=1)
        fig.add_hline(y=70, line=dict(color=COLORS["loss"],  width=1, dash="dot"), row=2, col=1)
        fig.add_hline(y=30, line=dict(color=COLORS["entry"], width=1, dash="dot"), row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor=COLORS["loss"],  opacity=0.05, row=2, col=1)
        fig.add_hrect(y0=0,  y1=30,  fillcolor=COLORS["entry"], opacity=0.05, row=2, col=1)

    elif ind == "Bollinger Bands" and "bb_upper" in df.columns:
        for col_name, label, color in [
            ("bb_upper", "Upper", COLORS["bb_u"]),
            ("bb_mid",   "Mid",   COLORS["bb_m"]),
            ("bb_lower", "Lower", COLORS["bb_l"]),
        ]:
            fig.add_trace(go.Scatter(
                x=df["open_time"], y=df[col_name],
                name=label, line=dict(color=color, width=1, dash="dot" if col_name != "bb_mid" else "solid"),
            ), row=2, col=1)

    fig.update_layout(
        height=500,
        paper_bgcolor="#080c14", plot_bgcolor="#080c14",
        font=dict(color="#e2e8f0", family="JetBrains Mono"),
        legend=dict(bgcolor="#0d1421", bordercolor="#1e2d4a", borderwidth=1,
                    font=dict(size=10)),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
    )
    fig.update_xaxes(gridcolor="#1e2d4a", zeroline=False)
    fig.update_yaxes(gridcolor="#1e2d4a", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    # ── Equity curve ──
    if n_trades > 0:
        eq_vals = [init_eq]
        eq_times = [df["open_time"].iloc[0]]
        for _, trade in df_tr.iterrows():
            eq_vals.append(eq_vals[-1] + trade["pnl_usdt"])
            eq_times.append(trade["close_ts"])

        fig_eq = go.Figure()
        for i in range(1, len(eq_vals)):
            color = COLORS["win"] if eq_vals[i] >= eq_vals[i-1] else COLORS["loss"]
            fig_eq.add_trace(go.Scatter(
                x=[eq_times[i-1], eq_times[i]],
                y=[eq_vals[i-1], eq_vals[i]],
                mode="lines",
                line=dict(color=color, width=2),
                showlegend=False,
                hovertemplate=f"{eq_times[i].strftime('%m-%d %H:%M')}<br>{eq_vals[i]:.4f} USDT<extra></extra>",
            ))
        fig_eq.add_trace(go.Scatter(
            x=eq_times, y=eq_vals,
            mode="markers",
            marker=dict(
                color=[COLORS["entry"]] + [COLORS["win"] if eq_vals[i] >= eq_vals[i-1] else COLORS["loss"]
                                            for i in range(1, len(eq_vals))],
                size=7,
            ),
            showlegend=False,
        ))
        fig_eq.update_layout(
            title=dict(text=t["equity_chart"], font=dict(size=12)),
            height=200,
            paper_bgcolor="#080c14", plot_bgcolor="#080c14",
            font=dict(color="#e2e8f0", family="JetBrains Mono", size=10),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        fig_eq.update_xaxes(gridcolor="#1e2d4a")
        fig_eq.update_yaxes(gridcolor="#1e2d4a")
        st.plotly_chart(fig_eq, use_container_width=True)

# ════════════════════
# TAB 2 — Trade Log
# ════════════════════
with tab2:
    if n_trades == 0:
        st.info("No trades executed." if lang == "en" else "거래 없음.")
    else:
        display = df_tr[["open_ts","close_ts","entry","exit","pnl_usdt","fee_usdt","hold_minutes","reason"]].copy()
        display.columns = [t["col_open"], t["col_close"], t["col_entry"], t["col_exit"],
                           t["col_pnl"], "Fee (USDT)", t["col_hold"], "Reason"]
        display[t["col_result"]] = display[t["col_pnl"]].apply(
            lambda x: "✅ WIN" if x > 0 else "❌ LOSS"
        )

        def color_row(val):
            try:
                return "color: #00ff88" if float(val) > 0 else "color: #ff4466" if float(val) < 0 else ""
            except Exception:
                return ""

        styled = display.style.applymap(color_row, subset=[t["col_pnl"]])
        st.dataframe(styled, use_container_width=True, hide_index=True)

# ════════════════════
# TAB 3 — AI Analysis
# ════════════════════
with tab3:
    if plan != "pro":
        st.warning(t["ai_pro_only"])
        st.markdown(
            f'<a href="https://sparkle488.gumroad.com" target="_blank">'
            f'<div style="background:linear-gradient(135deg,#7c3aed,#00d4ff);color:#fff;'
            f'text-align:center;padding:10px;border-radius:8px;font-size:0.85rem;'
            f'font-weight:700;cursor:pointer;max-width:220px;">{t["buy_pro"]}</div></a>',
            unsafe_allow_html=True,
        )
    else:
        if st.button(t["ai_btn"]):
            with st.spinner(t["ai_loading"]):
                api_key = get_deepseek_key()
                if not api_key:
                    st.error("DeepSeek API key not configured.")
                else:
                    summary = f"""
Indicator: {ind}
Symbol: {symbol}, TF: {tf}, Candles: {candles}
Strategy: {strategy_text}
Trades: {n_trades}, Wins: {wins}, Losses: {losses}, WR: {winrate}%
Total PnL: {total_pnl:.4f} USDT
Avg Hold: {avg_hold:.0f} min
Max Loss: {max_loss:.4f} USDT
Max Consec Loss: {consec}
"""
                    if lang == "ko":
                        prompt = f"""다음 백테스트 결과를 분석해주세요.

{summary}

다음 항목으로 분석해주세요:
1. **전체 성과 요약** (2~3문장, 쉬운 언어)
2. **전략의 강점** (잘 작동한 부분)
3. **주요 문제점** 2~3가지
4. **구체적 개선 제안** 2~3가지 (파라미터 수치 포함)

마크다운 형식으로 답변해주세요."""
                    else:
                        prompt = f"""Analyze this backtest result:

{summary}

Provide:
1. **Performance Summary** (2-3 sentences, plain English)
2. **Strategy Strengths** (what worked)
3. **Key Issues** (2-3 problems)
4. **Improvement Suggestions** (2-3 specific changes with numbers)

Reply in markdown format."""

                    try:
                        resp = requests.post(
                            "https://api.deepseek.com/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}",
                                     "Content-Type": "application/json"},
                            json={"model": "deepseek-chat",
                                  "messages": [{"role": "user", "content": prompt}],
                                  "max_tokens": 800, "temperature": 0.3},
                            timeout=30,
                        )
                        answer = resp.json()["choices"][0]["message"]["content"]
                        st.markdown(
                            f'<div style="background:#0d1421;border:1px solid #7c3aed;'
                            f'border-radius:10px;padding:20px;font-family:JetBrains Mono,monospace;'
                            f'font-size:0.8rem;line-height:1.8;">{answer}</div>',
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        st.error(f"AI error: {e}")
