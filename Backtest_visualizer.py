import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io, re, os, json
from datetime import datetime

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Backtest Result Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DeepSeek AI ───────────────────────────────────────────────
def get_ai_key():
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        return os.environ.get("DEEPSEEK_API_KEY", "")

# ── Language strings ──────────────────────────────────────────
def get_texts(lang="en"):
    en = {
        "title": "📊 Backtest Result Visualizer",
        "subtitle": "Upload your bot's CSV output and visualize performance instantly.",
        "sidebar_lang": "🇰🇷 한국어",
        "sidebar_plan": "🔑 Plan",
        "upload_trades": "Upload TRADES CSV",
        "upload_summary": "Upload SUMMARY CSV",
        "upload_result": "Upload RESULT CSV (optional)",
        "drop_hint": "CSV files exported from your trading bot",
        "tab_overview": "Overview",
        "tab_trades": "Trade Log",
        "tab_equity": "Equity Curve",
        "tab_ai": "AI Analysis",
        "total_pnl": "Total PnL",
        "winrate": "Win Rate",
        "trades": "Trades",
        "avg_pnl": "Avg PnL/Trade",
        "max_win": "Max Win",
        "max_loss": "Max Loss",
        "consec_loss": "Max Consec. Losses",
        "avg_hold": "Avg Hold Time",
        "minutes": "min",
        "no_file": "👆 Upload your TRADES CSV to get started",
        "no_summary": "Upload SUMMARY CSV for overview stats",
        "ai_btn": "🤖 Analyze with AI",
        "ai_loading": "Analyzing...",
        "ai_pro_only": "🔑 AI Analysis is available on Pro plan",
        "plan_free": "Free Plan",
        "plan_pro": "💎 Pro Plan",
        "free_features": ["Upload & visualize CSV", "Equity curve", "Trade log table"],
        "pro_features": ["Everything in Free", "AI pattern analysis", "Improvement suggestions", "Export report"],
        "enter_code": "🔑 Enter Subscription Code",
        "apply_code": "Apply Code",
        "code_ok": "💎 Pro plan activated!",
        "code_fail": "❌ Invalid code",
        "how_subscribe": "🛒 How to Subscribe",
        "sub_steps": ["1. Choose a plan below", "2. Pay via Gumroad — get code by email", "3. Enter code above"],
        "buy_pro": "💎 Buy Pro",
        "trade_open": "Open Time",
        "trade_close": "Close Time",
        "trade_side": "Side",
        "trade_entry": "Entry",
        "trade_exit": "Exit",
        "trade_pnl": "PnL (USDT)",
        "trade_hold": "Hold (min)",
        "equity_title": "Price & Equity Curve",
        "no_result_file": "Upload RESULT CSV to see equity curve with price overlay",
        "equity_from_trades": "Equity curve (from trades)",
    }
    ko = {
        "title": "📊 백테스트 결과 시각화",
        "subtitle": "봇이 출력한 CSV 파일을 업로드하면 성과를 바로 시각화합니다.",
        "sidebar_lang": "🇺🇸 English",
        "sidebar_plan": "🔑 플랜",
        "upload_trades": "TRADES CSV 업로드",
        "upload_summary": "SUMMARY CSV 업로드",
        "upload_result": "RESULT CSV 업로드 (선택)",
        "drop_hint": "트레이딩 봇이 출력한 CSV 파일",
        "tab_overview": "개요",
        "tab_trades": "거래 내역",
        "tab_equity": "에쿼티 커브",
        "tab_ai": "AI 분석",
        "total_pnl": "총 PnL",
        "winrate": "승률",
        "trades": "거래 횟수",
        "avg_pnl": "평균 PnL",
        "max_win": "최대 수익",
        "max_loss": "최대 손실",
        "consec_loss": "최대 연속 손실",
        "avg_hold": "평균 보유시간",
        "minutes": "분",
        "no_file": "👆 TRADES CSV를 업로드하세요",
        "no_summary": "SUMMARY CSV를 업로드하면 통계가 표시됩니다",
        "ai_btn": "🤖 AI 분석 실행",
        "ai_loading": "분석 중...",
        "ai_pro_only": "🔑 AI 분석은 Pro 플랜에서 사용 가능합니다",
        "plan_free": "무료 플랜",
        "plan_pro": "💎 Pro 플랜",
        "free_features": ["CSV 업로드 & 시각화", "에쿼티 커브", "거래 내역 테이블"],
        "pro_features": ["무료 플랜 전체 포함", "AI 패턴 분석", "개선 제안", "리포트 내보내기"],
        "enter_code": "🔑 구독 코드 입력",
        "apply_code": "코드 적용",
        "code_ok": "💎 Pro 플랜 활성화!",
        "code_fail": "❌ 잘못된 코드입니다",
        "how_subscribe": "🛒 구독 방법",
        "sub_steps": ["1. 아래에서 플랜 선택", "2. Gumroad 결제 → 이메일로 코드 수신", "3. 위에 코드 입력"],
        "buy_pro": "💎 Pro 구매",
        "trade_open": "진입 시간",
        "trade_close": "청산 시간",
        "trade_side": "방향",
        "trade_entry": "진입가",
        "trade_exit": "청산가",
        "trade_pnl": "PnL (USDT)",
        "trade_hold": "보유(분)",
        "equity_title": "가격 & 에쿼티 커브",
        "no_result_file": "RESULT CSV를 업로드하면 가격과 에쿼티를 함께 볼 수 있습니다",
        "equity_from_trades": "에쿼티 커브 (거래 기반)",
    }
    return ko if lang == "ko" else en

# ── Subscription codes ────────────────────────────────────────
def load_pro_codes():
    try:
        raw = st.secrets.get("PRO_CODES", "")
        if raw:
            return [c.strip() for c in raw.split(",") if c.strip()]
    except Exception:
        pass
    return []

def check_code(code):
    pro_codes = load_pro_codes()
    return code.strip().upper() in [c.upper() for c in pro_codes]

# ── Session state ─────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "plan" not in st.session_state:
    st.session_state.plan = "free"

lang = st.session_state.lang
t = get_texts(lang)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    if st.button(t["sidebar_lang"]):
        st.session_state.lang = "ko" if lang == "en" else "en"
        st.rerun()

    st.divider()

    # Plan display
    st.markdown(f"### {t['sidebar_plan']}")
    plan_now = st.session_state.plan

    free_box = "border:1px solid #4b5563;border-radius:8px;padding:10px;margin-bottom:8px;"
    pro_box  = "border:2px solid #f59e0b;border-radius:8px;padding:10px;margin-bottom:8px;"

    st.markdown(
        f'<div style="{free_box if plan_now=="free" else "border:1px solid #374151;border-radius:8px;padding:10px;margin-bottom:8px;"}">'
        f'<b>{"✅ " if plan_now=="free" else ""}{t["plan_free"]}</b><br>'
        + "".join(f'<span style="font-size:0.8rem;color:#9ca3af;">· {f}</span><br>' for f in t["free_features"])
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="{pro_box if plan_now=="pro" else "border:1px solid #374151;border-radius:8px;padding:10px;margin-bottom:8px;"}">'
        f'<b>{"✅ " if plan_now=="pro" else ""}💎 Pro — $19/mo</b><br>'
        + "".join(f'<span style="font-size:0.8rem;color:#9ca3af;">· {f}</span><br>' for f in t["pro_features"])
        + "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # Code input
    st.markdown(f"#### {t['enter_code']}")
    code_input = st.text_input("", placeholder="BT-XXXX-XXXX", type="password", label_visibility="collapsed")
    if st.button(t["apply_code"]):
        if check_code(code_input):
            st.session_state.plan = "pro"
            st.success(t["code_ok"])
            st.rerun()
        else:
            st.error(t["code_fail"])

    st.divider()

    # How to subscribe
    st.markdown(f"#### {t['how_subscribe']}")
    for step in t["sub_steps"]:
        st.markdown(f'<span style="font-size:0.8rem;color:#9ca3af;">{step}</span>', unsafe_allow_html=True)

    GUMROAD_PRO = "https://sparkle488.gumroad.com"
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<a href="{GUMROAD_PRO}" target="_blank">'
            f'<div style="background:#f59e0b;color:#000;text-align:center;padding:6px;'
            f'border-radius:8px;font-size:0.8rem;cursor:pointer;">{t["buy_pro"]}</div></a>',
            unsafe_allow_html=True,
        )

# ── Main ──────────────────────────────────────────────────────
st.markdown(f"## {t['title']}")
st.markdown(f'<p style="color:#9ca3af;">{t["subtitle"]}</p>', unsafe_allow_html=True)
st.divider()

# File upload
col_a, col_b, col_c = st.columns(3)
with col_a:
    trades_file = st.file_uploader(t["upload_trades"], type="csv", key="trades")
with col_b:
    summary_file = st.file_uploader(t["upload_summary"], type="csv", key="summary")
with col_c:
    result_file = st.file_uploader(t["upload_result"], type="csv", key="result")

if not trades_file:
    st.info(t["no_file"])
    st.stop()

# ── Load data ─────────────────────────────────────────────────
df_trades  = pd.read_csv(trades_file)
df_summary = pd.read_csv(summary_file) if summary_file else None
df_result  = pd.read_csv(result_file)  if result_file  else None

# ── Tabs ──────────────────────────────────────────────────────
tabs = st.tabs([t["tab_overview"], t["tab_trades"], t["tab_equity"], t["tab_ai"]])

# ════════════════════════════════════════════
# TAB 1 — Overview
# ════════════════════════════════════════════
with tabs[0]:
    if df_summary is not None:
        s = df_summary.iloc[0]

        pnl   = float(s.get("total_pnl_usdt", 0))
        wr    = float(s.get("winrate_pct", 0))
        n     = int(s.get("trades", 0))
        avg   = float(s.get("avg_pnl_usdt", 0))
        mxw   = float(s.get("max_win_usdt", 0))
        mxl   = float(s.get("max_loss_usdt", 0))
        mcl   = int(s.get("max_consec_losses", 0))

        avg_hold = df_trades["hold_minutes"].mean() if "hold_minutes" in df_trades.columns else 0

        pnl_color  = "#22c55e" if pnl >= 0 else "#ef4444"
        wr_color   = "#22c55e" if wr >= 50 else "#f59e0b"

        c1, c2, c3, c4 = st.columns(4)
        metric_style = "background:#111827;border-radius:10px;padding:16px;text-align:center;"
        def metric_card(col, label, value, color="#f9fafb"):
            col.markdown(
                f'<div style="{metric_style}">'
                f'<div style="color:#6b7280;font-size:0.8rem;">{label}</div>'
                f'<div style="color:{color};font-size:1.6rem;font-weight:700;">{value}</div>'
                f'</div>', unsafe_allow_html=True
            )

        metric_card(c1, t["total_pnl"],  f"{pnl:+.2f} USDT", pnl_color)
        metric_card(c2, t["winrate"],    f"{wr:.1f}%",        wr_color)
        metric_card(c3, t["trades"],     str(n))
        metric_card(c4, t["avg_pnl"],    f"{avg:+.3f} USDT",  "#22c55e" if avg >= 0 else "#ef4444")

        st.markdown("<br>", unsafe_allow_html=True)
        c5, c6, c7, c8 = st.columns(4)
        metric_card(c5, t["max_win"],     f"+{mxw:.3f} USDT", "#22c55e")
        metric_card(c6, t["max_loss"],    f"{mxl:.3f} USDT",  "#ef4444")
        metric_card(c7, t["consec_loss"], str(mcl),            "#f59e0b")
        metric_card(c8, t["avg_hold"],    f"{avg_hold:.0f} {t['minutes']}")

    else:
        st.info(t["no_summary"])

        # Basic stats from trades only
        if not df_trades.empty and "pnl_usdt" in df_trades.columns:
            pnl_total = df_trades["pnl_usdt"].sum()
            wins      = (df_trades["pnl_usdt"] > 0).sum()
            total     = len(df_trades)
            wr        = wins / total * 100 if total > 0 else 0

            c1, c2, c3 = st.columns(3)
            pnl_color = "#22c55e" if pnl_total >= 0 else "#ef4444"
            metric_style = "background:#111827;border-radius:10px;padding:16px;text-align:center;"
            def metric_card2(col, label, value, color="#f9fafb"):
                col.markdown(
                    f'<div style="{metric_style}">'
                    f'<div style="color:#6b7280;font-size:0.8rem;">{label}</div>'
                    f'<div style="color:{color};font-size:1.6rem;font-weight:700;">{value}</div>'
                    f'</div>', unsafe_allow_html=True
                )
            metric_card2(c1, t["total_pnl"], f"{pnl_total:+.2f} USDT", pnl_color)
            metric_card2(c2, t["winrate"],   f"{wr:.1f}%", "#22c55e" if wr >= 50 else "#f59e0b")
            metric_card2(c3, t["trades"],    str(total))

# ════════════════════════════════════════════
# TAB 2 — Trade Log
# ════════════════════════════════════════════
with tabs[1]:
    display = df_trades.copy()

    rename_map = {}
    if "open_ts"      in display.columns: rename_map["open_ts"]      = t["trade_open"]
    if "close_ts"     in display.columns: rename_map["close_ts"]     = t["trade_close"]
    if "side"         in display.columns: rename_map["side"]         = t["trade_side"]
    if "entry"        in display.columns: rename_map["entry"]        = t["trade_entry"]
    if "exit"         in display.columns: rename_map["exit"]         = t["trade_exit"]
    if "pnl_usdt"     in display.columns: rename_map["pnl_usdt"]     = t["trade_pnl"]
    if "hold_minutes" in display.columns: rename_map["hold_minutes"] = t["trade_hold"]

    display = display.rename(columns=rename_map)

    # Color PnL column
    pnl_col = t["trade_pnl"]

    def color_pnl(val):
        try:
            v = float(val)
            return "color: #22c55e" if v > 0 else "color: #ef4444" if v < 0 else ""
        except Exception:
            return ""

    styled = display.style.applymap(color_pnl, subset=[pnl_col]) if pnl_col in display.columns else display.style
    st.dataframe(styled, use_container_width=True)

# ════════════════════════════════════════════
# TAB 3 — Equity Curve
# ════════════════════════════════════════════
with tabs[2]:
    if df_result is not None and "equity" in df_result.columns and "close" in df_result.columns:
        df_result["ts"] = pd.to_datetime(df_result["ts"])

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=df_result["ts"], y=df_result["close"],
                name="Price", line=dict(color="#3b82f6", width=1.2),
                hovertemplate="%{x}<br>Price: %{y:.2f}<extra></extra>",
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df_result["ts"], y=df_result["equity"],
                name="Equity (USDT)", line=dict(color="#f97316", width=2),
                hovertemplate="%{x}<br>Equity: %{y:.4f}<extra></extra>",
            ),
            secondary_y=True,
        )

        # Mark trades
        if not df_trades.empty:
            for _, row in df_trades.iterrows():
                pnl_val = float(row.get("pnl_usdt", 0))
                color   = "#22c55e" if pnl_val >= 0 else "#ef4444"
                fig.add_vline(
                    x=pd.Timestamp(row["open_ts"]).timestamp() * 1000,
                    line=dict(color=color, width=1, dash="dot"),
                    annotation_text="E" if lang == "en" else "진입",
                    annotation_font_size=9,
                )

        fig.update_layout(
            title=t["equity_title"],
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#f9fafb"),
            legend=dict(bgcolor="#1e293b"),
            hovermode="x unified",
            height=420,
        )
        fig.update_xaxes(gridcolor="#1e293b")
        fig.update_yaxes(gridcolor="#1e293b", secondary_y=False, title_text="Price (USDT)")
        fig.update_yaxes(gridcolor="#1e293b", secondary_y=True,  title_text="Equity (USDT)")

        st.plotly_chart(fig, use_container_width=True)

    else:
        # Simple equity from trades
        st.info(t["no_result_file"])

        if not df_trades.empty and "pnl_usdt" in df_trades.columns:
            eq = df_trades["pnl_usdt"].cumsum()
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=list(range(1, len(eq)+1)), y=eq,
                mode="lines+markers",
                line=dict(color="#f97316", width=2),
                marker=dict(color=["#22c55e" if v >= 0 else "#ef4444" for v in df_trades["pnl_usdt"]], size=8),
                name=t["equity_from_trades"],
            ))
            fig2.update_layout(
                paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                font=dict(color="#f9fafb"),
                height=360,
                xaxis_title="Trade #",
                yaxis_title="Cumulative PnL (USDT)",
            )
            fig2.update_xaxes(gridcolor="#1e293b")
            fig2.update_yaxes(gridcolor="#1e293b")
            st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════
# TAB 4 — AI Analysis (Pro only)
# ════════════════════════════════════════════
with tabs[3]:
    if plan_now != "pro":
        st.warning(t["ai_pro_only"])
        st.markdown(
            f'<a href="{GUMROAD_PRO}" target="_blank">'
            f'<div style="background:#f59e0b;color:#000;text-align:center;padding:10px;'
            f'border-radius:8px;font-size:0.9rem;cursor:pointer;max-width:200px;">{t["buy_pro"]}</div></a>',
            unsafe_allow_html=True,
        )
    else:
        if st.button(t["ai_btn"]):
            with st.spinner(t["ai_loading"]):
                # Build prompt
                summary_text = df_summary.to_string(index=False) if df_summary is not None else "N/A"
                trades_text  = df_trades.to_string(index=False)

                if lang == "ko":
                    prompt = f"""다음은 암호화폐 자동매매 봇의 백테스트 결과입니다.

[요약]
{summary_text}

[거래 내역]
{trades_text}

다음을 분석해주세요:
1. 전체 성과 요약 (쉬운 언어로)
2. 반복되는 패턴 (진입/청산 타이밍, 보유 시간)
3. 가장 큰 문제점 2~3가지
4. 구체적인 개선 제안 2~3가지

마크다운 형식으로 답변해주세요."""
                else:
                    prompt = f"""Here is a backtest result from a crypto trading bot.

[Summary]
{summary_text}

[Trade Log]
{trades_text}

Please analyze:
1. Overall performance summary (plain English)
2. Repeating patterns (entry/exit timing, hold duration)
3. Top 2-3 issues
4. 2-3 specific improvement suggestions

Reply in markdown format."""

                try:
                    import requests
                    api_key = get_ai_key()
                    if not api_key:
                        st.error("DeepSeek API key not configured.")
                    else:
                        resp = requests.post(
                            "https://api.deepseek.com/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                            json={
                                "model": "deepseek-chat",
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 1000,
                                "temperature": 0.3,
                            },
                            timeout=30,
                        )
                        result = resp.json()
                        answer = result["choices"][0]["message"]["content"]
                        st.markdown(answer)
                except Exception as e:
                    st.error(f"AI error: {e}")