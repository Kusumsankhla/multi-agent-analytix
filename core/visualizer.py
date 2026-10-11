import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class VisualizerEngine:
    """
    Advanced Realistic Kinetic Visualization Engine.
    Constructs publication-grade, interactive Plotly charts with kinetic motion,
    realistic glowing aesthetic effects, dynamic growth trajectory tracing,
    and step-by-step playback controls:
    1. Kinetic Growth Motion Chart / Progressive Trajectory Spline
    2. Progressive Motion Bar & Comparative Ranking Dynamics
    3. Executive Composition Donut with Center KPI Metrics
    4. Hierarchical Treemap Decomposition
    5. Statistical Dispersion Box & Outlier Engine
    6. Multi-Metric Segment Radar Comparison
    """

    THEME_TEMPLATE = "plotly_dark"
    COLOR_PALETTE = ["#38BDF8", "#10B981", "#818CF8", "#F59E0B", "#EC4899", "#8B5CF6", "#14B8A6", "#06B6D4"]
    BG_PAPER = "rgba(11, 15, 25, 0.95)"
    BG_PLOT = "rgba(15, 23, 42, 0.55)"
    GRID_COLOR = "rgba(148, 163, 184, 0.12)"

    @staticmethod
    def format_metric(val: Any) -> str:
        """Utility for executive-grade, human-readable metric formatting."""
        if val is None or pd.isna(val):
            return "N/A"
        try:
            val_f = float(val)
            abs_v = abs(val_f)
            if abs_v >= 1_000_000_000:
                return f"{val_f / 1_000_000_000:.2f}B"
            elif abs_v >= 1_000_000:
                return f"{val_f / 1_000_000:.2f}M"
            elif abs_v >= 1_000:
                return f"{val_f / 1_000:.1f}K"
            elif 0 < abs_v < 0.01:
                return f"{val_f:.4f}"
            elif isinstance(val_f, float):
                return f"{val_f:.2f}" if abs_v != int(abs_v) else f"{int(val_f)}"
            return str(val)
        except Exception:
            return str(val)

    @classmethod
    def detect_is_growth_or_trend(cls, question: str, dim_col: str, df: pd.DataFrame) -> bool:
        """Determines if the question or dataset structure implies growth, time-series, or sequential trend."""
        q_lower = question.lower()
        dim_lower = dim_col.lower()

        growth_keywords = [
            "growth", "grow", "trend", "time", "date", "over time", "month", "day",
            "year", "quarter", "history", "evolution", "progress", "trajectory",
            "change", "period", "from", "to", "since", "across time", "speed",
            "velocity", "progression", "timeline", "annual", "monthly", "daily",
            "rate", "delta", "increase", "decrease"
        ]
        if any(kw in q_lower for kw in growth_keywords):
            return True

        dim_keywords = [
            "date", "time", "month", "year", "day", "quarter", "period", "week",
            "epoch", "timestamp", "dt", "yr", "mo", "orderdate", "trans_date"
        ]
        if any(kw in dim_lower for kw in dim_keywords):
            return True

        # Check if values in dim_col look chronological or sequential
        sample_vals = [str(x).strip() for x in df[dim_col].head(8)]
        is_date_like = any(
            any(char in val for char in ["-", "/", ":"]) or
            (val.isdigit() and len(val) == 4 and 1990 <= int(val) <= 2030) or
            any(m in val.lower() for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "q1", "q2", "q3", "q4"])
            for val in sample_vals
        )
        return is_date_like

    @classmethod
    def build_kinetic_growth_chart(
        cls,
        df: pd.DataFrame,
        dim_col: str,
        metric_cols: List[str],
        question: str
    ) -> go.Figure:
        """
        Builds a realistic kinetic growth spline chart with:
        - Shaded glowing gradient area
        - Dual-ring markers and neon bloom trail
        - Active moving beacon (motion head)
        - Net growth rate / delta badge
        - Global peak and trough annotations
        - Frame-by-frame motion playback controls & timeline slider
        """
        primary_metric = metric_cols[0]
        x_vals = [str(x) for x in df[dim_col].tolist()]
        y_vals = [float(v) if pd.notnull(v) else 0.0 for v in df[primary_metric].tolist()]
        n = len(df)

        start_val = y_vals[0]
        end_val = y_vals[-1]
        total_delta = end_val - start_val
        total_pct = ((end_val - start_val) / abs(start_val) * 100) if start_val != 0 else 0.0
        is_positive = total_delta >= 0

        # Colors & Visual styling
        accent_color = "#10B981" if is_positive else "#38BDF8"
        line_color = "#38BDF8"
        area_color = "rgba(56, 189, 248, 0.14)"

        # Stable Y-axis bounds
        y_min = min(y_vals)
        y_max = max(y_vals)
        y_span = (y_max - y_min) if y_max != y_min else (abs(y_max) if y_max != 0 else 1.0)
        y_lower = min(0.0, y_min - 0.15 * y_span) if y_min >= 0 else (y_min - 0.2 * y_span)
        y_upper = y_max + 0.25 * y_span

        fig = go.Figure()

        # 1. Full Path Guide (Ghost trajectory trace)
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color="rgba(148, 163, 184, 0.25)", width=2, dash="dot"),
            name="Target Trajectory",
            hoverinfo="skip"
        ))

        # 2. Neon Bloom Glow Trace
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color=line_color, width=9, shape="spline", smoothing=1.3),
            opacity=0.3,
            showlegend=False,
            hoverinfo="skip"
        ))

        # 3. Main Sharp Spline Line with Gradient Area Fill
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            line=dict(color=line_color, width=3.5, shape="spline", smoothing=1.3),
            marker=dict(size=8, color="#FFFFFF", line=dict(color=line_color, width=2.5)),
            fill="tozeroy",
            fillcolor=area_color,
            name=f"{primary_metric} Trajectory",
            hovertemplate="<b>%{x}</b><br>" + f"{primary_metric}: <b>" + "%{y:,.2f}</b><extra></extra>"
        ))

        # 4. Active Kinetic Beacon Runner
        fig.add_trace(go.Scatter(
            x=[x_vals[-1]],
            y=[y_vals[-1]],
            mode="markers+text",
            marker=dict(size=14, color=accent_color, line=dict(color="#FFFFFF", width=3)),
            text=[f"Current: {cls.format_metric(y_vals[-1])}"],
            textposition="top center",
            textfont=dict(color="#FFFFFF", size=11, family="Inter, sans-serif"),
            name="Kinetic Runner",
            showlegend=False
        ))

        # Annotations
        annotations = []
        # Growth Rate Banner Chip
        growth_chip_bg = "rgba(16, 185, 129, 0.2)" if is_positive else "rgba(244, 63, 94, 0.2)"
        growth_chip_border = "#10B981" if is_positive else "#F43F5E"
        growth_symbol = "▲" if is_positive else "▼"
        annotations.append(dict(
            xref="paper", yref="paper",
            x=0.99, y=1.12,
            xanchor="right", yanchor="top",
            text=f"<b>{growth_symbol} Growth: {total_pct:+.1f}%</b> ({cls.format_metric(total_delta)})",
            showarrow=False,
            font=dict(size=12, color="#FFFFFF", family="Inter, sans-serif"),
            bgcolor=growth_chip_bg,
            bordercolor=growth_chip_border,
            borderwidth=1.5,
            borderpad=6
        ))

        # Peak badge
        if n >= 2:
            max_idx = int(np.argmax(y_vals))
            annotations.append(dict(
                x=x_vals[max_idx], y=y_vals[max_idx],
                text=f"⭐ Peak: {cls.format_metric(y_vals[max_idx])}",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
                arrowcolor="#38BDF8", ax=0, ay=-35,
                font=dict(size=10, color="#38BDF8", family="Inter, sans-serif"),
                bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#38BDF8", borderwidth=1, borderpad=4
            ))

        # Trough badge if distinct
        if n >= 3:
            min_idx = int(np.argmin(y_vals))
            if min_idx != max_idx:
                annotations.append(dict(
                    x=x_vals[min_idx], y=y_vals[min_idx],
                    text=f"🔻 Low: {cls.format_metric(y_vals[min_idx])}",
                    showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
                    arrowcolor="#F43F5E", ax=0, ay=35,
                    font=dict(size=10, color="#F43F5E", family="Inter, sans-serif"),
                    bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#F43F5E", borderwidth=1, borderpad=4
                ))

        # Subsample frames if dataset is large (keeps 60fps performance)
        frame_indices = list(range(1, n + 1)) if n <= 25 else sorted(list(set(np.linspace(1, n, 25, dtype=int))))

        frames = []
        steps = []
        for i in frame_indices:
            sub_x = x_vals[:i]
            sub_y = y_vals[:i]
            curr_x = x_vals[i - 1]
            curr_y = y_vals[i - 1]
            step_growth = ((curr_y - start_val) / abs(start_val) * 100) if start_val != 0 else 0.0

            frame_data = [
                # Guide trace (constant)
                go.Scatter(x=x_vals, y=y_vals, mode="lines", line=dict(color="rgba(148, 163, 184, 0.25)", width=2, dash="dot")),
                # Bloom trace
                go.Scatter(x=sub_x, y=sub_y, mode="lines", line=dict(color=line_color, width=9, shape="spline", smoothing=1.3), opacity=0.3),
                # Main spline + area
                go.Scatter(x=sub_x, y=sub_y, mode="lines+markers", line=dict(color=line_color, width=3.5, shape="spline", smoothing=1.3), marker=dict(size=8, color="#FFFFFF", line=dict(color=line_color, width=2.5)), fill="tozeroy", fillcolor=area_color),
                # Kinetic runner
                go.Scatter(x=[curr_x], y=[curr_y], mode="markers+text", marker=dict(size=14, color=accent_color, line=dict(color="#FFFFFF", width=3)), text=[f"<b>{cls.format_metric(curr_y)}</b> ({step_growth:+.1f}%)"], textposition="top center", textfont=dict(color="#FFFFFF", size=11, family="Inter, sans-serif"))
            ]
            frames.append(go.Frame(data=frame_data, name=curr_x))

            steps.append(dict(
                method="animate",
                args=[[curr_x], dict(mode="immediate", frame=dict(duration=250, redraw=True), transition=dict(duration=180, easing="cubic-in-out"))],
                label=curr_x
            ))

        fig.frames = frames

        updatemenus = [dict(
            type="buttons",
            direction="left",
            showactive=False,
            x=0.0, y=1.16,
            xanchor="left", yanchor="top",
            pad=dict(t=0, r=10),
            buttons=[
                dict(
                    label="▶ Play Growth Motion",
                    method="animate",
                    args=[None, dict(frame=dict(duration=450, redraw=True), fromcurrent=True, mode="immediate", transition=dict(duration=300, easing="cubic-in-out"))]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                ),
                dict(
                    label="⏮ Replay",
                    method="animate",
                    args=[[frames[0].name], dict(frame=dict(duration=200, redraw=True), mode="immediate", transition=dict(duration=150, easing="cubic-in-out"))]
                ),
                dict(
                    label="📊 Full View",
                    method="animate",
                    args=[[frames[-1].name], dict(frame=dict(duration=200, redraw=True), mode="immediate", transition=dict(duration=150, easing="cubic-in-out"))]
                )
            ]
        )]

        sliders = [dict(
            active=len(steps) - 1,
            steps=steps,
            currentvalue=dict(
                font=dict(size=12, color="#38BDF8", family="Inter, sans-serif"),
                prefix="Growth Timeline: ",
                visible=True,
                xanchor="center"
            ),
            transition=dict(duration=250, easing="cubic-in-out"),
            pad=dict(t=35, b=10),
            len=0.92,
            x=0.04, y=-0.14,
            bgcolor="#1E293B",
            activebgcolor="#38BDF8",
            bordercolor="rgba(56, 189, 248, 0.3)",
            tickcolor="#64748B",
            font=dict(color="#94A3B8", size=10)
        )]

        fig.update_layout(
            title=dict(
                text=f"📈 <b>Verified Growth Trajectory</b>: {primary_metric} across {dim_col}",
                font=dict(size=16, color="#F8FAFC", family="Inter, sans-serif"),
                x=0.0, xanchor="left"
            ),
            xaxis=dict(
                type="category",
                categoryorder="array",
                categoryarray=x_vals,
                tickangle=-30,
                gridcolor=cls.GRID_COLOR,
                linecolor="rgba(148, 163, 184, 0.2)",
                tickfont=dict(color="#94A3B8", size=11)
            ),
            yaxis=dict(
                range=[y_lower, y_upper],
                gridcolor=cls.GRID_COLOR,
                linecolor="rgba(148, 163, 184, 0.2)",
                tickfont=dict(color="#94A3B8", size=11),
                zeroline=True,
                zerolinecolor="rgba(148, 163, 184, 0.25)"
            ),
            annotations=annotations,
            updatemenus=updatemenus,
            sliders=sliders,
            template=cls.THEME_TEMPLATE,
            height=490,
            margin=dict(l=55, r=45, t=90, b=90),
            paper_bgcolor=cls.BG_PAPER,
            plot_bgcolor=cls.BG_PLOT,
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center", font=dict(color="#94A3B8", size=11))
        )
        return fig

    @classmethod
    def build_progressive_motion_bar_chart(
        cls,
        df: pd.DataFrame,
        dim_col: str,
        numeric_cols: List[str],
        question: str
    ) -> go.Figure:
        """
        Builds a realistic progressive motion bar chart with:
        - Continuous gradient intensity and neon bar outlines
        - Progressive category-by-category motion frames
        - Overlay trajectory progression spline across bars
        - Benchmark average reference line
        - Playback controls & slider
        """
        primary_metric = numeric_cols[0]
        secondary_metric = numeric_cols[1] if len(numeric_cols) > 1 else None

        x_vals = [str(x) for x in df[dim_col].tolist()]
        y_vals = [float(v) if pd.notnull(v) else 0.0 for v in df[primary_metric].tolist()]
        n = len(df)

        y_min = min(y_vals)
        y_max = max(y_vals)
        y_span = (y_max - y_min) if y_max != y_min else (abs(y_max) if y_max != 0 else 1.0)
        y_lower = min(0.0, y_min - 0.1 * y_span) if y_min >= 0 else (y_min - 0.2 * y_span)
        y_upper = y_max + 0.25 * y_span

        fig = go.Figure()

        val_texts = [cls.format_metric(v) for v in y_vals]

        # 1. Bar Trace with Continuous Gradient Coloring & Neon Border
        fig.add_trace(go.Bar(
            x=x_vals,
            y=y_vals,
            name=f"{primary_metric}",
            text=val_texts,
            textposition="outside",
            textfont=dict(color="#F8FAFC", size=11, family="Inter, sans-serif"),
            marker=dict(
                color=y_vals,
                colorscale="Viridis",
                line=dict(color="#38BDF8", width=1.5)
            ),
            hovertemplate="<b>%{x}</b><br>" + f"{primary_metric}: <b>" + "%{y:,.2f}</b><extra></extra>"
        ))

        # 2. Progression Trajectory Spline Curve across the bars
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            name="Progression Spline",
            line=dict(color="#10B981", width=3, shape="spline", smoothing=1.3),
            marker=dict(size=9, color="#10B981", line=dict(color="#FFFFFF", width=2)),
            hovertemplate="<b>%{x}</b><br>Progression: <b>%{y:,.2f}</b><extra></extra>"
        ))

        # If secondary metric exists (e.g. Profit alongside Sales), add secondary bar trace
        if secondary_metric:
            y2_vals = [float(v) if pd.notnull(v) else 0.0 for v in df[secondary_metric].tolist()]
            fig.add_trace(go.Bar(
                x=x_vals,
                y=y2_vals,
                name=f"{secondary_metric}",
                text=[cls.format_metric(v) for v in y2_vals],
                textposition="outside",
                textfont=dict(color="#A7F3D0", size=10, family="Inter, sans-serif"),
                marker=dict(
                    color="#10B981",
                    line=dict(color="#34D399", width=1.2)
                ),
                hovertemplate="<b>%{x}</b><br>" + f"{secondary_metric}: <b>" + "%{y:,.2f}</b><extra></extra>"
            ))

        # Annotations: Benchmark Average Reference Line
        avg_val = float(np.mean(y_vals))
        annotations = []
        fig.add_hline(
            y=avg_val,
            line_dash="dash",
            line_color="rgba(148, 163, 184, 0.45)",
            line_width=1.5,
            annotation_text=f"Benchmark Avg: {cls.format_metric(avg_val)}",
            annotation_position="top right",
            annotation_font=dict(color="#94A3B8", size=11, family="Inter, sans-serif")
        )

        # Leader badge
        max_idx = int(np.argmax(y_vals))
        annotations.append(dict(
            x=x_vals[max_idx], y=y_vals[max_idx],
            text=f"🏆 Top: {x_vals[max_idx]} ({cls.format_metric(y_vals[max_idx])})",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
            arrowcolor="#10B981", ax=0, ay=-35,
            font=dict(size=11, color="#10B981", family="Inter, sans-serif"),
            bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="#10B981", borderwidth=1.2, borderpad=4
        ))

        # Frames for progressive dynamics
        frame_indices = list(range(1, n + 1)) if n <= 25 else sorted(list(set(np.linspace(1, n, 25, dtype=int))))

        frames = []
        steps = []
        for i in frame_indices:
            sub_x = x_vals[:i]
            sub_y = y_vals[:i]
            curr_x = x_vals[i - 1]

            frame_data = [
                # Bar
                go.Bar(
                    x=sub_x, y=sub_y,
                    text=[cls.format_metric(v) for v in sub_y],
                    textposition="outside",
                    marker=dict(
                        color=sub_y,
                        colorscale="Viridis",
                        cmin=min(y_vals),
                        cmax=max(y_vals),
                        line=dict(color="#38BDF8", width=1.5)
                    )
                ),
                # Spline
                go.Scatter(
                    x=sub_x, y=sub_y,
                    mode="lines+markers",
                    line=dict(color="#10B981", width=3, shape="spline", smoothing=1.3),
                    marker=dict(size=9, color="#10B981", line=dict(color="#FFFFFF", width=2))
                )
            ]
            if secondary_metric:
                sub_y2 = [float(v) if pd.notnull(v) else 0.0 for v in df[secondary_metric].iloc[:i].tolist()]
                frame_data.append(go.Bar(
                    x=sub_x, y=sub_y2,
                    text=[cls.format_metric(v) for v in sub_y2],
                    textposition="outside",
                    marker=dict(color="#10B981", line=dict(color="#34D399", width=1.2))
                ))

            frames.append(go.Frame(data=frame_data, name=curr_x))

            steps.append(dict(
                method="animate",
                args=[[curr_x], dict(mode="immediate", frame=dict(duration=250, redraw=True), transition=dict(duration=180, easing="cubic-in-out"))],
                label=curr_x
            ))

        fig.frames = frames

        updatemenus = [dict(
            type="buttons",
            direction="left",
            showactive=False,
            x=0.0, y=1.16,
            xanchor="left", yanchor="top",
            pad=dict(t=0, r=10),
            buttons=[
                dict(
                    label="▶ Play Progression & Growth",
                    method="animate",
                    args=[None, dict(frame=dict(duration=450, redraw=True), fromcurrent=True, mode="immediate", transition=dict(duration=300, easing="cubic-in-out"))]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                ),
                dict(
                    label="⏮ Replay",
                    method="animate",
                    args=[[frames[0].name], dict(frame=dict(duration=200, redraw=True), mode="immediate", transition=dict(duration=150, easing="cubic-in-out"))]
                ),
                dict(
                    label="📊 All Items",
                    method="animate",
                    args=[[frames[-1].name], dict(frame=dict(duration=200, redraw=True), mode="immediate", transition=dict(duration=150, easing="cubic-in-out"))]
                )
            ]
        )]

        sliders = [dict(
            active=len(steps) - 1,
            steps=steps,
            currentvalue=dict(
                font=dict(size=12, color="#38BDF8", family="Inter, sans-serif"),
                prefix="Progression: ",
                visible=True,
                xanchor="center"
            ),
            transition=dict(duration=250, easing="cubic-in-out"),
            pad=dict(t=35, b=10),
            len=0.92,
            x=0.04, y=-0.14,
            bgcolor="#1E293B",
            activebgcolor="#38BDF8",
            bordercolor="rgba(56, 189, 248, 0.3)",
            tickcolor="#64748B",
            font=dict(color="#94A3B8", size=10)
        )]

        fig.update_layout(
            barmode="group" if secondary_metric else "relative",
            title=dict(
                text=f"📊 <b>Verified Progression & Distribution</b>: {primary_metric} by {dim_col}",
                font=dict(size=16, color="#F8FAFC", family="Inter, sans-serif"),
                x=0.0, xanchor="left"
            ),
            xaxis=dict(
                type="category",
                categoryorder="array",
                categoryarray=x_vals,
                tickangle=-30,
                gridcolor=cls.GRID_COLOR,
                linecolor="rgba(148, 163, 184, 0.2)",
                tickfont=dict(color="#94A3B8", size=11)
            ),
            yaxis=dict(
                range=[y_lower, y_upper],
                gridcolor=cls.GRID_COLOR,
                linecolor="rgba(148, 163, 184, 0.2)",
                tickfont=dict(color="#94A3B8", size=11),
                zeroline=True,
                zerolinecolor="rgba(148, 163, 184, 0.25)"
            ),
            annotations=annotations,
            updatemenus=updatemenus,
            sliders=sliders,
            template=cls.THEME_TEMPLATE,
            height=490,
            margin=dict(l=55, r=45, t=90, b=90),
            paper_bgcolor=cls.BG_PAPER,
            plot_bgcolor=cls.BG_PLOT,
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center", font=dict(color="#94A3B8", size=11))
        )
        return fig

    @classmethod
    def build_executive_donut_chart(
        cls,
        df: pd.DataFrame,
        dim_col: str,
        primary_metric: str
    ) -> Optional[go.Figure]:
        """Builds an executive-grade composition donut with center KPI metrics and realistic slice pulling."""
        if len(df) < 2 or not (df[primary_metric] > 0).all():
            return None

        top_df = df.head(8)
        total_val = float(df[primary_metric].sum())
        top_name = str(top_df[dim_col].iloc[0])
        top_share = (float(top_df[primary_metric].iloc[0]) / total_val * 100) if total_val > 0 else 0.0

        pull_list = [0.06] + [0.0] * (len(top_df) - 1)

        fig_donut = px.pie(
            top_df,
            names=dim_col,
            values=primary_metric,
            title=f"🍩 <b>Proportional Share</b>: {primary_metric}",
            hole=0.55,
            color_discrete_sequence=cls.COLOR_PALETTE,
            template=cls.THEME_TEMPLATE
        )
        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent+label",
            pull=pull_list,
            marker=dict(line=dict(color="#0B0F19", width=2.5)),
            hovertemplate="<b>%{label}</b><br>Value: <b>%{value:,.2f}</b><br>Share: <b>%{percent}</b><extra></extra>"
        )

        fig_donut.add_annotation(
            text=f"<b>{cls.format_metric(total_val)}</b><br><span style='font-size:10px; color:#94A3B8;'>TOTAL {primary_metric.upper()[:10]}</span><br><span style='font-size:10px; color:#10B981;'>Top: {top_share:.1f}%</span>",
            x=0.5, y=0.5,
            font=dict(size=14, color="#F8FAFC", family="Inter, sans-serif"),
            showarrow=False
        )

        fig_donut.update_layout(
            margin=dict(l=25, r=25, t=55, b=25),
            height=410,
            paper_bgcolor=cls.BG_PAPER,
            showlegend=False,
            font=dict(color="#E2E8F0")
        )
        return fig_donut

    @classmethod
    def build_executive_treemap(
        cls,
        df: pd.DataFrame,
        dim_col: str,
        primary_metric: str
    ) -> Optional[go.Figure]:
        """Builds a hierarchical treemap decomposition with clean gradient depth."""
        if len(df) < 3 or not (df[primary_metric] > 0).all():
            return None
        try:
            fig_treemap = px.treemap(
                df,
                path=[dim_col],
                values=primary_metric,
                color=primary_metric,
                color_continuous_scale="Tealgrn",
                title=f"🗂️ <b>Treemap Decomposition</b>: {primary_metric}",
                template=cls.THEME_TEMPLATE
            )
            fig_treemap.update_traces(
                marker=dict(line=dict(color="#0F172A", width=1.5)),
                hovertemplate="<b>%{label}</b><br>Value: <b>%{value:,.2f}</b><extra></extra>"
            )
            fig_treemap.update_layout(
                margin=dict(l=15, r=15, t=55, b=15),
                height=410,
                paper_bgcolor=cls.BG_PAPER,
                font=dict(color="#E2E8F0")
            )
            return fig_treemap
        except Exception:
            return None

    @classmethod
    def build_executive_box_plot(
        cls,
        df: pd.DataFrame,
        primary_metric: str
    ) -> Optional[go.Figure]:
        """Builds a statistical dispersion box & outlier plot with jittered glowing points."""
        if len(df) < 3:
            return None

        fig_box = go.Figure()
        fig_box.add_trace(go.Box(
            y=df[primary_metric],
            name=primary_metric,
            boxpoints="all",
            jitter=0.35,
            pointpos=-1.8,
            boxmean="sd",
            marker=dict(color="#818CF8", size=6, line=dict(color="#38BDF8", width=1)),
            line=dict(color="#38BDF8", width=2),
            fillcolor="rgba(56, 189, 248, 0.18)"
        ))
        fig_box.update_layout(
            title=f"📦 <b>Statistical Dispersion & Outlier Box Plot</b> ({primary_metric})",
            template=cls.THEME_TEMPLATE,
            height=410,
            margin=dict(l=45, r=40, t=55, b=35),
            paper_bgcolor=cls.BG_PAPER,
            plot_bgcolor=cls.BG_PLOT,
            font=dict(color="#E2E8F0"),
            yaxis=dict(gridcolor=cls.GRID_COLOR)
        )
        return fig_box

    @classmethod
    def build_executive_radar_chart(
        cls,
        df: pd.DataFrame,
        dim_col: str,
        numeric_cols: List[str]
    ) -> Optional[go.Figure]:
        """Builds a multi-metric radar comparison with glowing vertices and semi-transparent fill."""
        if len(numeric_cols) < 2 or len(df) < 3:
            return None

        top_df = df.head(5)
        fig_radar = go.Figure()
        radar_metrics = numeric_cols[:4]

        for idx, r in top_df.iterrows():
            r_vals = [r[m] for m in radar_metrics]
            r_vals.append(r_vals[0])
            theta_vals = radar_metrics + [radar_metrics[0]]

            fig_radar.add_trace(go.Scatterpolar(
                r=r_vals,
                theta=theta_vals,
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.15)" if idx == 0 else None,
                line=dict(width=2.5),
                marker=dict(size=6),
                name=str(r[dim_col])
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, gridcolor=cls.GRID_COLOR, linecolor="rgba(148, 163, 184, 0.2)"),
                angularaxis=dict(gridcolor=cls.GRID_COLOR, linecolor="rgba(148, 163, 184, 0.2)")
            ),
            title="🕸️ <b>Multi-Metric Segment Radar Comparison</b>",
            template=cls.THEME_TEMPLATE,
            height=410,
            margin=dict(l=45, r=45, t=55, b=35),
            paper_bgcolor=cls.BG_PAPER,
            plot_bgcolor=cls.BG_PLOT,
            font=dict(color="#E2E8F0")
        )
        return fig_radar

    @classmethod
    def generate_chart_suite(
        cls, 
        columns: List[str], 
        rows: List[List[Any]], 
        question: str,
        stats_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive dictionary of interactive, motion-enabled Plotly figures.
        Returns:
        - primary: go.Figure (Kinetic growth spline or progressive motion bar chart with play/pause motion controls)
        - growth_motion: Optional[go.Figure] (Dedicated kinetic growth trajectory spline)
        - donut: Optional[go.Figure] (Proportional share with center KPI metric)
        - treemap: Optional[go.Figure] (Hierarchical tree decomposition)
        - box: Optional[go.Figure] (Statistical dispersion box & outlier plot)
        - radar: Optional[go.Figure] (Multi-metric radar comparison)
        """
        if not rows or len(columns) < 2:
            return {}

        df = pd.DataFrame(rows, columns=columns)
        dim_col = columns[0]

        # Identify numeric columns
        numeric_cols = []
        for c in columns[1:]:
            if pd.api.types.is_numeric_dtype(df[c]) or any(isinstance(val, (int, float)) for val in df[c]):
                df[c] = pd.to_numeric(df[c], errors="coerce")
                numeric_cols.append(c)

        if not numeric_cols:
            return {}

        primary_metric = numeric_cols[0]
        is_growth_trend = cls.detect_is_growth_or_trend(question, dim_col, df)

        charts: Dict[str, Any] = {}

        # ----------------------------------------------------------------------
        # 1. Primary Chart (Kinetic Growth Spline or Progressive Motion Bar Chart)
        # ----------------------------------------------------------------------
        if is_growth_trend or len(df) > 10:
            charts["primary"] = cls.build_kinetic_growth_chart(
                df=df,
                dim_col=dim_col,
                metric_cols=numeric_cols,
                question=question
            )
        else:
            charts["primary"] = cls.build_progressive_motion_bar_chart(
                df=df,
                dim_col=dim_col,
                numeric_cols=numeric_cols,
                question=question
            )

        # ----------------------------------------------------------------------
        # 2. Dedicated Kinetic Growth Trajectory (Always generated when len(df) >= 2)
        # ----------------------------------------------------------------------
        if len(df) >= 2:
            charts["growth_motion"] = cls.build_kinetic_growth_chart(
                df=df,
                dim_col=dim_col,
                metric_cols=numeric_cols,
                question=question
            )

        # ----------------------------------------------------------------------
        # 3. Composition Donut Chart with Center KPI
        # ----------------------------------------------------------------------
        donut_fig = cls.build_executive_donut_chart(df, dim_col, primary_metric)
        if donut_fig:
            charts["donut"] = donut_fig

        # ----------------------------------------------------------------------
        # 4. Hierarchical Treemap
        # ----------------------------------------------------------------------
        treemap_fig = cls.build_executive_treemap(df, dim_col, primary_metric)
        if treemap_fig:
            charts["treemap"] = treemap_fig

        # ----------------------------------------------------------------------
        # 5. Statistical Distribution / Outlier Box Plot
        # ----------------------------------------------------------------------
        box_fig = cls.build_executive_box_plot(df, primary_metric)
        if box_fig:
            charts["box"] = box_fig

        # ----------------------------------------------------------------------
        # 6. Multi-Metric Radar Comparison
        # ----------------------------------------------------------------------
        radar_fig = cls.build_executive_radar_chart(df, dim_col, numeric_cols)
        if radar_fig:
            charts["radar"] = radar_fig

        return charts

