from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from database import get_connection


def fetch_records():
    conn = get_connection()
    try:
        query = """
            SELECT a.accident_id, a.accident_datetime, l.region, l.road_name,
                   a.vehicle_type, a.severity, a.weather
            FROM accidents a
            JOIN locations l ON l.location_id = a.location_id
            ORDER BY a.accident_datetime
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    if not df.empty:
        df["accident_datetime"] = pd.to_datetime(df["accident_datetime"], errors="coerce")
        df["hour"] = df["accident_datetime"].dt.hour
        df["date"] = df["accident_datetime"].dt.date
        df["month"] = df["accident_datetime"].dt.to_period("M").astype(str)
        df["day_name"] = df["accident_datetime"].dt.day_name()
    return df


def build_dashboard_data(records=None):
    df = records if records is not None else fetch_records()
    if df.empty:
        return {
            "records": df, "total": 0, "fatal": 0, "serious": 0, "locations": 0,
            "missing": {"date/time": 0, "region": 0, "vehicle type": 0, "severity": 0},
            "hourly": [], "top_locations": [], "severity": [], "vehicles": [],
            "monthly": [], "avg_per_day": 0,
        }

    missing = {}
    for field, column in [
        ("date/time", "accident_datetime"), ("region", "region"),
        ("vehicle type", "vehicle_type"), ("severity", "severity")
    ]:
        missing[field] = int(df[column].isna().sum()) if column in df else len(df)

    hourly_series = df.dropna(subset=["hour"]).groupby("hour").size().reindex(range(24), fill_value=0)
    top_locations = df.groupby("region").size().sort_values(ascending=False).head(10)
    severity_series = df["severity"].fillna("Missing").value_counts()
    vehicle_series = df["vehicle_type"].fillna("Missing").value_counts().head(10)
    monthly_series = df.dropna(subset=["month"]).groupby("month").size().sort_index()
    days = max(df["date"].nunique(), 1)

    return {
        "records": df,
        "total": int(len(df)),
        "fatal": int((df["severity"] == "Fatal").sum()),
        "serious": int((df["severity"] == "Serious").sum()),
        "locations": int(df["region"].nunique()),
        "missing": missing,
        "hourly": [{"label": f"{int(k):02d}:00", "count": int(v)} for k, v in hourly_series.items()],
        "top_locations": [{"label": str(k), "count": int(v)} for k, v in top_locations.items()],
        "severity": [{"label": str(k), "count": int(v)} for k, v in severity_series.items()],
        "vehicles": [{"label": str(k), "count": int(v)} for k, v in vehicle_series.items()],
        "monthly": [{"label": str(k), "count": int(v)} for k, v in monthly_series.items()],
        "avg_per_day": round(float(np.mean(df.groupby("date").size().values)), 2) if not df["date"].isna().all() else 0,
    }


def build_time_summary(df):
    if df.empty:
        return []
    grouped = df.dropna(subset=["accident_datetime"]).copy()
    grouped["period"] = grouped["accident_datetime"].dt.to_period("M").astype(str)
    out = grouped.groupby("period").agg(
        accident_count=("accident_id", "count"),
        fatal_count=("severity", lambda s: int((s == "Fatal").sum())),
        serious_count=("severity", lambda s: int((s == "Serious").sum())),
    ).reset_index().sort_values("period", ascending=False)
    return out.to_dict("records")


def build_location_summary(df):
    if df.empty:
        return []
    out = df.groupby("region").agg(
        accident_count=("accident_id", "count"),
        fatal_count=("severity", lambda s: int((s == "Fatal").sum())),
        serious_count=("severity", lambda s: int((s == "Serious").sum())),
    ).reset_index().sort_values("accident_count", ascending=False).head(20)
    return out.to_dict("records")


def build_severity_summary(df):
    if df.empty:
        return []
    out = df["severity"].fillna("Missing").value_counts().rename_axis("severity").reset_index(name="count")
    out["percentage"] = (out["count"] / max(len(df), 1) * 100).round(1)
    return out.to_dict("records")


def build_charts(df, return_bytes=False):
    outputs = {}
    chart_specs = [
        ("daily", "Accident Counts by Month", "month", "Monthly accident count", "Monthly trend"),
        ("severity", "Recorded Severity Distribution", "severity", "Number of records", "Severity"),
        ("vehicle", "Accidents by Vehicle Type", "vehicle_type", "Number of records", "Vehicle type"),
    ]
    for name, title, column, ylabel, xlabel in chart_specs:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        if df.empty or column not in df.columns:
            ax.text(0.5, 0.5, "No accident data available", ha="center", va="center")
            ax.set_axis_off()
        elif name == "daily":
            values = df.dropna(subset=["accident_datetime"]).copy()
            values["month"] = values["accident_datetime"].dt.to_period("M").astype(str)
            counts = values.groupby("month").size().sort_index()
            ax.bar(counts.index.astype(str), counts.values)
            ax.tick_params(axis="x", rotation=45)
            ax.set_ylabel(ylabel)
            ax.set_xlabel(xlabel)
        else:
            counts = df[column].fillna("Missing").value_counts().head(12)
            ax.bar(counts.index.astype(str), counts.values)
            ax.tick_params(axis="x", rotation=30)
            ax.set_ylabel(ylabel)
            ax.set_xlabel(xlabel)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        if return_bytes:
            buffer = BytesIO()
            fig.savefig(buffer, format="png", dpi=130, bbox_inches="tight")
            outputs[name] = buffer.getvalue()
            buffer.close()
        else:
            outputs[name] = f"/charts/{name}.png"
        plt.close(fig)
    return outputs
