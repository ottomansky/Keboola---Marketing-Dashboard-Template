import os
from datetime import timedelta
from datetime import date as _date
from numbers import Number
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Marketing Metrics", layout="wide")

# Global styles for card visuals
st.markdown(
    """
    <style>
      .card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px 18px;
        box-shadow: 0 1px 2px rgba(16,24,40,0.05);
        height: 100%;
        min-height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        text-align: center;
        gap: 6px;
        position: relative;
      }
      /* Sidebar footer positioning using flex to avoid overlap */
      [data-testid="stSidebar"] > div:first-child { display: flex; flex-direction: column; min-height: 100vh; }
      .sidebar-footer { margin-top: auto; text-align: center; padding: 8px 0 10px; }
      .card-title {
        color: #374151;
        font-size: 1.0rem;
        font-weight: 400;
        margin-bottom: 2px;
        white-space: nowrap;
      }
      .card-title .title-strong { font-weight: 700; color: #111827; }
      .card-title .unit { font-weight: 400; color: #6b7280; margin-left: 6px; }
      /* Floating help icon top-left per card */
      .help-floating { position: absolute; top: 10px; left: 10px; }
      .help-floating .icon {
        width: 18px; height: 18px; border-radius: 50%;
        background: #eff6ff; color: #2563eb; font-weight: 700;
        font-size: 12px; line-height: 18px; text-align: center;
        border: 1px solid #2563eb; cursor: default; display: inline-flex; align-items: center; justify-content: center;
      }
      .help-floating .tip {
        display: none; position: absolute; top: 22px; left: 0;
        background: #111827; color: #ffffff; padding: 8px 12px; border-radius: 6px;
        font-size: 14px; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        text-align: left; z-index: 1000;
      }
      .help-floating:hover .tip { display: block; }
      .card-value {
        color: #111827;
        font-weight: 500;
        font-size: 2.0rem;
      }
      /* Ensure equal gaps horizontally between Streamlit columns */
      div[data-testid="stHorizontalBlock"] { gap: 16px; }
      .row-spacer { height: 16px; }
      /* Pill label alignment */
      .pill-label { display:flex; align-items:center; height:57px; font-size:0.95rem; color:#374151; }
      .pill-label.right { justify-content:flex-end; }
      .pill-label.left { justify-content:flex-start; }
      .pill-mid { display:flex; align-items:center; justify-content:center; height:0px; position:relative; top:-12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Use Keboola-mounted file only
data_path = os.path.join(os.sep, 'data', 'in', 'tables', 'marketing_metrics.csv')
_mtime = os.path.getmtime(data_path)
df = pd.read_csv(data_path)

# Normalize schema to have period_date
if 'date' in df.columns:
    df['period_date'] = pd.to_datetime(df['date'], errors='coerce')
else:
    df['period_date'] = pd.to_datetime(df['year_month'].astype(str) + '-01', errors='coerce')

df['year'] = df['period_date'].dt.year.astype('Int64')
df['month'] = df['period_date'].dt.month.astype('Int64')

lang = 'en'
keboola_logo = "https://www.startupjobs.cz/cdn-cgi/image/w=2688,h=946,f=avif,webp,q=90,fit=cover/https://images-assets.startupjobs.cz/COVER/7213/8b7046b9b5b0f95d5e9ec09d33fdac68.png"

# Filters
with st.sidebar:
    # Top-left Keboola branding above filters
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:8px; margin:4px 0 8px 0;'>
          <img src='{keboola_logo}' alt='Keboola' style='height:28px; border-radius:6px; border:1px solid #e5e7eb;'>
          <div style='font-size:12px; color:#6b7280;'>Powered by Keboola</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Filters header with an inline delta help tooltip next to Quick ranges
    st.header("Filters")
    # Shipping input highlighted when empty
    _ship_val = float(st.session_state.get('shipping_cost', 0.0) or 0.0)
    _ship_bg = "#fde2e7" if _ship_val == 0.0 else "#ffffff"
    st.markdown(f"""
        <div style='background:{_ship_bg}; border:1px solid #f1f5f9; padding:8px 10px; border-radius:8px; margin-bottom:6px;'>
        <div style='font-size:0.9rem; color:#374151; margin-bottom:4px;'>Shipping cost (EUR per order)</div>
        </div>
    """, unsafe_allow_html=True)
    st.number_input(
        "Shipping cost (EUR per order)",
        min_value=0.0,
        step=0.1,
        key='shipping_cost',
        label_visibility='collapsed'
    )
    min_date = pd.to_datetime(df['period_date'].min()).date()
    max_date = pd.to_datetime(df['period_date'].max()).date()
    _options = [
            "Custom",
            "This month",
            "Last month",
            "QTD",
            "YTD",
            "Last 30d",
            "Last 60d",
            "Last 90d",
    ]
    _today = _date.today()
    ui_max_date = max(_today, max_date)
    _anchor_today = _today

    def range_for_preset(preset_label: str):
        anchor = pd.to_datetime(_anchor_today)
        if preset_label == "This month":
            p = anchor.to_period('M')
            s, e = p.start_time.date(), p.end_time.date()
        elif preset_label == "Last month":
            prev = (anchor - pd.DateOffset(months=1)).to_period('M')
            s, e = prev.start_time.date(), prev.end_time.date()
        elif preset_label == "QTD":
            q = anchor.to_period('Q')
            s, e = q.start_time.date(), anchor.date()
        elif preset_label == "YTD":
            y = anchor.to_period('Y')
            s, e = y.start_time.date(), anchor.date()
        elif preset_label.endswith('d'):
            days = int(preset_label.split()[1].replace('d',''))
            s, e = (anchor - timedelta(days=days-1)).date(), anchor.date()
        else:
            s, e = (min_date, _anchor_today)
        # clamp to UI bounds (data filter will naturally limit to available rows)
        return (max(s, min_date), min(e, ui_max_date))

    def match_preset_for_range(s: _date, e: _date) -> str:
        # Compare against computed ranges; return matching label else Custom
        for opt in _options:
            if opt == "Custom":
                continue
            rs, re = range_for_preset(opt)
            if rs == s and re == e:
                return opt
        return "Custom"

    # Initialize session defaults
    if 'preset' not in st.session_state:
        st.session_state['preset'] = "Last month"
    if 'date_range' not in st.session_state:
        st.session_state['date_range'] = range_for_preset(st.session_state['preset'])
    if 'granularity' not in st.session_state:
        st.session_state['granularity'] = "Monthly"
    if 'shipping_cost' not in st.session_state:
        st.session_state['shipping_cost'] = 0.0

    def _as_date_list(dr) -> list:
        if isinstance(dr, (list, tuple)):
            seq = list(dr)
        elif hasattr(dr, 'tolist'):
            try:
                seq = dr.tolist()
            except Exception:
                seq = [dr]
        else:
            seq = [dr]
        out = []
        for v in seq:
            try:
                out.append(pd.to_datetime(v).date())
            except Exception:
                pass
        return out

    def _normalize_range(dr):
        vals = _as_date_list(dr)
        if len(vals) >= 2:
            return (vals[0], vals[1])
        if len(vals) == 1:
            return (vals[0], vals[0])
        return (min_date, min_date)

    def _expand_to_full_months(dr):
        s, e = _normalize_range(dr)
        s_p = pd.to_datetime(s).to_period('M')
        e_p = pd.to_datetime(e).to_period('M')
        s_full = max(min_date, s_p.start_time.date())
        e_full = min(ui_max_date, e_p.end_time.date())
        return (s_full, e_full)

    def _on_preset_change():
        if st.session_state['preset'] != "Custom":
            desired = range_for_preset(st.session_state['preset'])
            if st.session_state.get('granularity', 'Monthly') == 'Monthly':
                desired = _expand_to_full_months(desired)
            st.session_state['date_range'] = desired

    def _on_date_change():
        s, e = _normalize_range(st.session_state['date_range'])
        if st.session_state.get('granularity', 'Monthly') == 'Monthly':
            expanded = _expand_to_full_months((s, e))
            # Snap picker to full months in Monthly mode
            st.session_state['date_range'] = expanded
            # Update preset to match expanded range if any
            matched = match_preset_for_range(expanded[0], expanded[1])
            st.session_state['preset'] = matched
            return
        matched = match_preset_for_range(s, e)
        st.session_state['preset'] = matched

    def _on_granularity_change():
        # When switching to Monthly, expand current range to full months and reflect in picker
        if st.session_state.get('granularity', 'Monthly') == 'Monthly':
            expanded = _expand_to_full_months(st.session_state['date_range'])
            st.session_state['date_range'] = expanded
            # Try set preset accordingly
            s, e = expanded
            st.session_state['preset'] = match_preset_for_range(s, e)

    # Widgets bound to session_state
    st.markdown("<div style='font-weight:600; margin-bottom:4px;'>Quick ranges</div>", unsafe_allow_html=True)
    preset = st.selectbox("Quick ranges", _options, key='preset', on_change=_on_preset_change, label_visibility='collapsed')
    date_range = st.date_input(
        "Date range",
        min_value=min_date,
        max_value=ui_max_date,
        key='date_range',
        on_change=_on_date_change
    )
    granularity = st.selectbox("Breakdown", ["Monthly", "Daily"], key='granularity', on_change=_on_granularity_change)
    # Table/Plot switch pill: Table | [toggle] | Plot
    _pill = st.columns([1, 0.5, 1])
    with _pill[0]:
        st.markdown("<div class='pill-label right'>Table</div>", unsafe_allow_html=True)
    with _pill[1]:
        if 'view_plot' not in st.session_state:
            st.session_state['view_plot'] = False
        st.markdown("<div class='pill-mid'>", unsafe_allow_html=True)
        st.toggle("Plot view", key='view_plot', label_visibility='collapsed')
        st.markdown("</div>", unsafe_allow_html=True)
    with _pill[2]:
        st.markdown("<div class='pill-label left'>Plot</div>", unsafe_allow_html=True)

    # Plot configuration (only relevant when Plot view is active)
    plot_options = [
        "Ad Costs vs Revenue vs MER",
        "MER vs CM3 vs CM2",
        "Revenue",
        "Orders",
        "CAC & ROI",
        "Costs breakdown: Google+Meta vs Revenue",
    ]
    st.selectbox("Plot type", plot_options, index=0, key='plot_type', disabled=(not st.session_state.get('view_plot', False)))

    # Final selected range from session_state (normalize to scalar dates)
    start_date, end_date = _normalize_range(st.session_state['date_range'])

    # If Monthly breakdown, expand selection to whole months (already synced to picker via callbacks)
    if granularity == "Monthly":
        _s = pd.to_datetime(start_date).to_period('M')
        _e = pd.to_datetime(end_date).to_period('M')
        start_date = max(min_date, _s.start_time.date())
        end_date = min(ui_max_date, _e.end_time.date())

    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)
    sel_mask = (df['period_date'] >= start_ts) & (df['period_date'] <= end_ts)

    # (Removed footer branding; branding shown above filters)

fdf = df[sel_mask].copy()

def t(key: str) -> str:
    labels = {
        'title': 'Marketing Metrics Dashboard',
        'orders': 'Orders',
        'revenue': 'Revenue',
        'cogs': 'COGS',
        'cm2': 'CM2',
        'ad_costs': 'Ad Costs',
        'cac': 'CAC',
        'mer': 'MER',
        'cm3': 'CM3',
        'roi': 'ROI',
        'aov': 'AOV',
        'breakdown': 'Breakdown',
        'period': 'Period',
        'google_costs': 'Google Costs',
        'meta_costs': 'Meta Costs',
    }
    return labels.get(key, key)

st.title(t('title'))

def render_card(label: str, value: float | str, unit: str | None = None, delta_pct: float | None = None, tooltip: str | None = None):
    display = value if isinstance(value, str) else f"{float(value):,.2f}"
    # Build title with unit inline, only metric name bold
    unit_html = f" <span class='unit'>(" + unit + ")</span>" if unit else ""
    title_text = f"<span class='title-strong'>{label}</span>{unit_html}"
    delta_html = ""
    # Accept numpy scalars too
    if isinstance(delta_pct, Number):
        up = delta_pct >= 0
        arrow = "▲" if up else "▼"
        try:
            delta_abs = float(abs(delta_pct))
        except Exception:
            delta_abs = 0.0
        color = "#16a34a" if up else "#dc2626"
        delta_html = f"<div style='font-size:0.9rem;color:{color}'>{arrow} {delta_abs:.2f}%</div>"
    st.markdown(f"""
        <div class="card">
          <div class="help-floating"><span class="icon">ℹ</span><div class="tip">{tooltip or ''}</div></div>
          <div class="card-title">{title_text}</div>
          <div class="card-value">{display}</div>
          {delta_html}
        </div>
    """, unsafe_allow_html=True)

# Precompute aggregates for selection
def compute_metrics(dff: pd.DataFrame) -> dict:
    orders = float(dff['orders'].sum())
    revenue = float(dff['revenue'].sum())
    cogs = float(dff['cost_of_goods_sold'].sum()) if 'cost_of_goods_sold' in dff.columns else 0.0
    # Include shipping cost per order into CM2
    ship_cost = float(st.session_state.get('shipping_cost', 0.0))
    cm2 = float(revenue - cogs - (ship_cost * orders))
    google = float(dff['google_costs'].sum())
    meta = float(dff['meta_costs'].sum())
    ad_costs = float(dff.get('ad_costs', dff['google_costs'] + dff['meta_costs']).sum())
    cm3 = float(cm2 - ad_costs)
    cac = float(ad_costs / orders) if orders else 0.0
    mer = float(revenue / ad_costs) if ad_costs else 0.0
    roi = float(cm3 / ad_costs) if ad_costs else 0.0
    aov = float(revenue / orders) if orders else 0.0
    return {
        'orders': orders,
        'revenue': revenue,
        'cogs': cogs,
        'cm2': cm2,
        'cm3': cm3,
        'ad_costs': ad_costs,
        'google': google,
        'meta': meta,
        'cac': cac,
        'mer': mer,
        'roi': roi,
        'aov': aov,
    }

def pct_change(curr: float, prev: float) -> float:
    if prev == 0:
        return 0.0
    return (curr - prev) / abs(prev) * 100.0

# Current metrics for selected range
curr = compute_metrics(fdf)

def _compute_prev_range(sel_start: pd.Timestamp, sel_end: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    preset = st.session_state.get('preset', 'Custom')
    gran = st.session_state.get('granularity', 'Monthly')
    # Helper periods
    sel_start_m = sel_start.to_period('M')
    sel_end_m = sel_end.to_period('M')
    if preset in ("This month", "Last month") and gran == "Monthly":
        prev_m = sel_start_m - 1
        return prev_m.start_time, prev_m.end_time
    if preset == "YTD" and gran == "Monthly":
        # Jan to current end month of previous year
        prev_start_y = (sel_start.to_period('Y') - 1).start_time
        prev_end_y = (sel_end_m - 12).end_time
        return prev_start_y, prev_end_y
    if preset == "QTD" and gran == "Monthly":
        # Previous full quarter
        curr_q = sel_end.to_period('Q')
        prev_q = curr_q - 1
        return prev_q.start_time, prev_q.end_time
    # Rolling windows like Last 30d/60d/90d or Custom: same-length immediately preceding
    window_days = (sel_end.normalize() - sel_start.normalize()).days + 1
    prev_end = sel_start.normalize() - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=window_days - 1)
    return prev_start, prev_end

prev_start, prev_end = _compute_prev_range(start_ts, end_ts)

prev_mask = (df['period_date'] >= prev_start) & (df['period_date'] <= prev_end)
prevdf = df[prev_mask]
prev = compute_metrics(prevdf)

eur = 'EUR'
pct = '%'

# Tooltips mapping
tooltips = {
    t('revenue'): 'Revenue = sum(totalPriceWithoutVat) from Shoptet orders, excluding cancelled lines',
    t('orders'): 'Orders = count of distinct Shoptet order codes, excluding cancelled',
    t('ad_costs'): 'Ad Costs = Google Costs + Meta Costs (+ Other, if present)',
    t('cac'): 'CAC = Ad Costs ÷ Orders',
    t('roi'): 'ROI = CM3 ÷ Ad Costs',
    t('mer'): 'MER = Revenue ÷ Ad Costs (unitless)',
    t('cm2'): 'CM2 = Revenue − COGS − Shipping (Shipping = shipping_cost × orders)',
    t('cm3'): 'CM3 = CM2 − Ad Costs',
    t('aov'): 'AOV = Revenue ÷ Orders',
    t('google_costs'): 'Google Costs = sum(advertiserAdCost) from GA4',
    t('meta_costs'): 'Meta Costs = sum(spend) from Meta Ads insights',
}

# First row: Revenue, Orders, Ad Costs, CAC, ROI
row1 = st.columns(5)
with row1[0]:
    render_card(t('revenue'), curr['revenue'], eur, pct_change(curr['revenue'], prev['revenue']), tooltips[t('revenue')])
with row1[1]:
    render_card(t('orders'), curr['orders'], None, pct_change(curr['orders'], prev['orders']), tooltips[t('orders')])
with row1[2]:
    render_card(t('ad_costs'), curr['ad_costs'], eur, pct_change(curr['ad_costs'], prev['ad_costs']), tooltips[t('ad_costs')])
with row1[3]:
    render_card(t('cac'), curr['cac'], eur, pct_change(curr['cac'], prev['cac']), tooltips[t('cac')])
with row1[4]:
    render_card(t('roi'), curr['roi'], pct, pct_change(curr['roi'], prev['roi']), tooltips[t('roi')])

# Second row: CM2, CM3, AOV, Google Costs, Meta Costs
st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)
row2 = st.columns(5)
with row2[0]:
    render_card(t('cm2'), curr['cm2'], eur, pct_change(curr['cm2'], prev['cm2']), tooltips[t('cm2')])
with row2[1]:
    render_card(t('cm3'), curr['cm3'], eur, pct_change(curr['cm3'], prev['cm3']), tooltips[t('cm3')])
with row2[2]:
    render_card(t('mer'), curr['mer'], None, pct_change(curr['mer'], prev['mer']), tooltips[t('mer')])
with row2[3]:
    render_card(t('google_costs'), curr['google'], eur, pct_change(curr['google'], prev['google']), tooltips[t('google_costs')])
with row2[4]:
    render_card(t('meta_costs'), curr['meta'], eur, pct_change(curr['meta'], prev['meta']), tooltips[t('meta_costs')])

st.divider()
st.subheader(t('breakdown'))

# Build breakdown table according to granularity
if st.session_state.get('granularity', 'Monthly') == "Daily":
    # Show selected range daily rows
    dff = fdf.copy()
    dff['date'] = dff['period_date'].dt.strftime('%Y-%m-%d')
    # Assemble daily view
    df_show = dff[['date', 'orders', 'google_costs', 'meta_costs', 'ad_costs', 'revenue', 'cost_of_goods_sold', 'cm2', 'cm3', 'cac', 'mer', 'roi', 'aov']].copy()
    df_show = df_show.sort_values('date')
    df_plot = df_show.copy()
    # Use string date as x to avoid month-start normalization
    df_plot['x'] = df_plot['date']
else:
    # Aggregate by month within the selected range only
    ydf = fdf.copy()
    ydf['year_month'] = ydf['period_date'].dt.to_period('M').astype(str)
    agg = ydf.groupby('year_month', as_index=False).agg(
        orders=('orders', 'sum'),
        google_costs=('google_costs', 'sum'),
        meta_costs=('meta_costs', 'sum'),
        other_costs=('other_costs', 'sum') if 'other_costs' in ydf.columns else ('orders', 'sum'),
        revenue=('revenue', 'sum'),
        cogs=('cost_of_goods_sold', 'sum')
    ).rename(columns={'cogs': 'cost_of_goods_sold'})
    agg['ad_costs'] = agg['google_costs'] + agg['meta_costs'] + (agg['other_costs'] if 'other_costs' in agg.columns else 0)
    # Adjust CM2 monthly with shipping cost per order
    _ship = float(st.session_state.get('shipping_cost', 0.0))
    agg['cm2'] = agg['revenue'] - agg['cost_of_goods_sold'] - (_ship * agg['orders'])
    agg['cm3'] = agg['cm2'] - agg['ad_costs']
    agg['cac'] = agg.apply(lambda r: (r['ad_costs'] / r['orders']) if r['orders'] > 0 else 0.0, axis=1)
    agg['mer'] = agg.apply(lambda r: (r['revenue'] / r['ad_costs']) if r['ad_costs'] > 0 else 0.0, axis=1)
    agg['roi'] = agg.apply(lambda r: (r['cm3'] / r['ad_costs']) if r['ad_costs'] > 0 else 0.0, axis=1)
    agg['aov'] = agg.apply(lambda r: (r['revenue'] / r['orders']) if r['orders'] > 0 else 0.0, axis=1)
    df_show = agg[['year_month', 'orders', 'google_costs', 'meta_costs', 'ad_costs', 'revenue', 'cost_of_goods_sold', 'cm2', 'cm3', 'cac', 'mer', 'roi', 'aov']].copy()
    df_show = df_show.sort_values('year_month')
    df_plot = df_show.copy()
    # Use month label as x for monthly plots to avoid first-of-month dates in tooltips
    df_plot['x'] = pd.to_datetime(df_plot['year_month'] + '-01', errors='coerce').dt.strftime('%b %Y')

if not st.session_state.get('view_plot', False):
    df_show = df_show.reset_index(drop=True)
    # format all non-date columns to 2 decimals for display
    display_df = df_show.copy()
    id_col = 'date' if 'date' in display_df.columns else ('year_month' if 'year_month' in display_df.columns else None)
    for _col in display_df.columns:
        if _col != id_col:
            display_df[_col] = display_df[_col].apply(lambda v: (f"{float(v):.2f}" if pd.notnull(v) else ""))
    _rows = min(12, len(df_show)) if len(df_show) else 12
    _row_height = 34
    _header_height = 38
    _padding = 16
    _height = _header_height + (_rows * _row_height) + _padding
    st.dataframe(display_df, use_container_width=True, height=_height, hide_index=True)
else:
    # Build modern Plotly time-series per selected plot type
    sel = st.session_state.get('plot_type', 'Ad Costs vs Revenue vs MER')
    _is_monthly = st.session_state.get('granularity', 'Monthly') == 'Monthly'
    _x_title = 'Month' if _is_monthly else 'Date'
    fig = go.Figure()
    if sel == 'Ad Costs vs Revenue vs MER':
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['revenue'], mode='lines', name='Revenue (EUR)',
            line=dict(color='#2563eb', width=2),
            hovertemplate=('Month=%{x}<br>Revenue (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>Revenue (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['ad_costs'], mode='lines', name='Ad Costs (EUR)',
            line=dict(color='#dc2626', width=2, dash='dash'),
            hovertemplate=('Month=%{x}<br>Ad Costs (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>Ad Costs (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['mer'].round(2), mode='lines', name='MER',
            line=dict(color='#10b981', width=2), yaxis='y2',
            hovertemplate=('Month=%{x}<br>MER=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>MER=%{y:.2f}<extra></extra>')
        ))
        fig.update_layout(yaxis2=dict(title='MER', overlaying='y', side='right', showgrid=False))
        y_title = 'Revenue / Ad Costs (EUR)'
    elif sel == 'MER vs CM3 vs CM2':
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['cm2'], mode='lines', name='CM2 (EUR)',
            line=dict(color='#2563eb', width=2),
            hovertemplate=('Month=%{x}<br>CM2 (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>CM2 (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['cm3'], mode='lines', name='CM3 (EUR)',
            line=dict(color='#dc2626', width=2, dash='dash'),
            hovertemplate=('Month=%{x}<br>CM3 (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>CM3 (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['mer'].round(2), mode='lines', name='MER',
            line=dict(color='#10b981', width=2), yaxis='y2',
            hovertemplate=('Month=%{x}<br>MER=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>MER=%{y:.2f}<extra></extra>')
        ))
        fig.update_layout(yaxis2=dict(title='MER', overlaying='y', side='right', showgrid=False))
        y_title = 'CM2 / CM3 (EUR)'
    elif sel == 'Revenue':
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['revenue'], mode='lines+markers', name='Revenue (EUR)',
            line=dict(color='#2563eb', width=2), marker=dict(size=4),
            hovertemplate=('Month=%{x}<br>Revenue (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>Revenue (EUR)=%{y:.2f}<extra></extra>')
        ))
        y_title = 'Revenue (EUR)'
    elif sel == 'Orders':
        fig.add_trace(go.Bar(
            x=df_plot['x'], y=df_plot['orders'], name='Orders', marker_color='#10b981', opacity=0.7,
            hovertemplate=('Month=%{x}<br>Orders=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>Orders=%{y:.2f}<extra></extra>')
        ))
        y_title = 'Orders'
    elif sel == 'CAC & ROI':
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['cac'], mode='lines', name='CAC (EUR)',
            line=dict(color='#7c3aed', width=2),
            hovertemplate=('Month=%{x}<br>CAC (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>CAC (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['roi'], mode='lines', name='ROI',
            line=dict(color='#f59e0b', width=2, dash='dot'), yaxis='y2',
            hovertemplate=('Month=%{x}<br>ROI=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>ROI=%{y:.2f}<extra></extra>')
        ))
        fig.update_layout(yaxis2=dict(title='ROI', overlaying='y', side='right', showgrid=False))
        y_title = 'CAC (EUR)'
    elif sel == 'Costs breakdown: Google+Meta vs Revenue':
        fig.add_trace(go.Bar(
            x=df_plot['x'], y=(df_plot['google_costs'] + df_plot['meta_costs']), name='Ad Costs (Google+Meta)',
            marker_color='#64748b', opacity=0.6,
            hovertemplate=('Month=%{x}<br>Ad Costs (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>Ad Costs (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.add_trace(go.Scatter(
            x=df_plot['x'], y=df_plot['revenue'], mode='lines', name='Revenue (EUR)',
            line=dict(color='#2563eb', width=2), yaxis='y2',
            hovertemplate=('Month=%{x}<br>Revenue (EUR)=%{y:.2f}<extra></extra>' if _is_monthly else 'Date=%{x}<br>Revenue (EUR)=%{y:.2f}<extra></extra>')
        ))
        fig.update_layout(yaxis2=dict(title='Revenue (EUR)', overlaying='y', side='right', showgrid=False))
        y_title = 'Ad Costs (EUR)'
    else:
        y_title = 'Value'
    fig.update_layout(
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title=_x_title), yaxis=dict(title=y_title, gridcolor='rgba(0,0,0,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)



