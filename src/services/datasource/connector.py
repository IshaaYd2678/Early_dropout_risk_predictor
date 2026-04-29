"""
Universal database connector for university data sources.

Supports:
  - PostgreSQL  (Banner, PeopleSoft, custom)
  - MySQL / MariaDB
  - Microsoft SQL Server  (Ellucian, Colleague)
  - Oracle  (Banner ODS)
  - SQLite  (local / dev)
  - CSV / Excel file upload
  - REST API  (Canvas LMS, Moodle, Blackboard)

Each source is registered in data/datasources.json and can be
tested, synced, and removed through the API without touching code.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# ── persistence ──────────────────────────────────────────────────────────────
REGISTRY_PATH = Path("data/datasources.json")
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {}


def _save_registry(reg: Dict[str, Any]) -> None:
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2, default=str)


# ── column mapping ────────────────────────────────────────────────────────────
# Maps arbitrary source column names → internal feature names.
# Override per-source via the `column_map` field when registering.
DEFAULT_COLUMN_MAP: Dict[str, str] = {
    # academic
    "gpa": "gpa",
    "grade_point_average": "gpa",
    "cumulative_gpa": "gpa",
    "attendance": "attendance_rate",
    "attendance_rate": "attendance_rate",
    "attend_pct": "attendance_rate",
    "submission_rate": "assignment_submission_rate",
    "assignment_submission_rate": "assignment_submission_rate",
    "exam_score": "exam_scores",
    "exam_scores": "exam_scores",
    "final_grade": "exam_scores",
    # engagement
    "lms_logins": "lms_login_frequency",
    "lms_login_frequency": "lms_login_frequency",
    "login_count": "lms_login_frequency",
    "late_submissions": "late_submissions",
    "late_count": "late_submissions",
    "participation": "participation_score",
    "participation_score": "participation_score",
    "forum_posts": "forum_posts",
    "discussion_posts": "forum_posts",
    "resource_access": "resource_access_count",
    "resource_access_count": "resource_access_count",
    "time_on_platform": "time_spent_hours",
    "time_spent_hours": "time_spent_hours",
    # contextual
    "semester": "semester",
    "term": "semester",
    "dept": "department",
    "department": "department",
    "faculty": "department",
    "gender": "gender",
    "sex": "gender",
    "ses": "socioeconomic_status",
    "socioeconomic_status": "socioeconomic_status",
    "region": "region",
    "location": "region",
    "financial_aid": "has_financial_aid",
    "has_financial_aid": "has_financial_aid",
    "part_time": "is_part_time",
    "is_part_time": "is_part_time",
    "first_gen": "is_first_generation",
    "is_first_generation": "is_first_generation",
    # identity
    "student_id": "student_id",
    "id": "student_id",
    "sid": "student_id",
    "dropped_out": "dropped_out",
    "dropout": "dropped_out",
    "withdrawn": "dropped_out",
}


def _apply_column_map(df: pd.DataFrame, custom_map: Dict[str, str]) -> pd.DataFrame:
    """Rename source columns to internal names."""
    merged = {**DEFAULT_COLUMN_MAP, **custom_map}
    rename = {src: dst for src, dst in merged.items() if src in df.columns}
    return df.rename(columns=rename)


# ── SQL helper ────────────────────────────────────────────────────────────────

def _build_engine(cfg: Dict[str, Any]):
    """Return a SQLAlchemy engine from a source config dict."""
    try:
        from sqlalchemy import create_engine, text  # noqa: F401
    except ImportError:
        raise RuntimeError("sqlalchemy is required for database connections. Run: pip install sqlalchemy")

    db_type = cfg["db_type"].lower()
    host = cfg.get("host", "localhost")
    port = cfg.get("port")
    database = cfg.get("database", "")
    username = cfg.get("username", "")
    password = cfg.get("password", "")

    if db_type == "postgresql":
        port = port or 5432
        try:
            import psycopg2  # noqa: F401
        except ImportError:
            raise RuntimeError("psycopg2-binary is required. Run: pip install psycopg2-binary")
        url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

    elif db_type in ("mysql", "mariadb"):
        port = port or 3306
        try:
            import pymysql  # noqa: F401
        except ImportError:
            raise RuntimeError("PyMySQL is required. Run: pip install PyMySQL")
        url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

    elif db_type in ("mssql", "sqlserver"):
        port = port or 1433
        try:
            import pyodbc  # noqa: F401
        except ImportError:
            raise RuntimeError("pyodbc is required. Run: pip install pyodbc")
        url = (
            f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        )

    elif db_type == "oracle":
        port = port or 1521
        try:
            import cx_Oracle  # noqa: F401
        except ImportError:
            raise RuntimeError("cx_Oracle is required. Run: pip install cx_Oracle")
        url = f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}"

    elif db_type == "sqlite":
        db_path = cfg.get("sqlite_path", "data/university.db")
        url = f"sqlite:///{db_path}"

    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    from sqlalchemy import create_engine
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})


# ── REST API helper ───────────────────────────────────────────────────────────

def _fetch_rest_api(cfg: Dict[str, Any]) -> pd.DataFrame:
    """Pull student data from a REST API (Canvas, Moodle, custom)."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests is required. Run: pip install requests")

    base_url = cfg["api_url"].rstrip("/")
    headers = {}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    if cfg.get("api_token"):
        headers["Authorization"] = f"Token {cfg['api_token']}"

    endpoint = cfg.get("endpoint", "/api/v1/students")
    params = cfg.get("params", {})

    all_records: List[Dict] = []
    url = f"{base_url}{endpoint}"

    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Handle both list and paginated {"results": [...], "next": "..."} shapes
        if isinstance(data, list):
            all_records.extend(data)
            url = None
        elif isinstance(data, dict):
            records = data.get("results") or data.get("data") or data.get("students") or []
            all_records.extend(records)
            url = data.get("next")  # follow pagination
            params = {}  # next URL already has params
        else:
            break

    return pd.DataFrame(all_records)


# ── public API ────────────────────────────────────────────────────────────────

class DataSourceConnector:
    """
    Manages registered data sources and pulls student data from them.

    Usage
    -----
    connector = DataSourceConnector()

    # Register a PostgreSQL source
    source_id = connector.register({
        "name": "Banner SIS",
        "type": "database",
        "db_type": "postgresql",
        "host": "db.university.edu",
        "port": 5432,
        "database": "sis_prod",
        "username": "readonly_user",
        "password": "secret",
        "query": "SELECT * FROM student_academic_view WHERE semester = 'FALL2025'",
    })

    # Test the connection
    ok, msg = connector.test(source_id)

    # Pull data into a DataFrame
    df = connector.fetch(source_id)
    """

    def register(self, config: Dict[str, Any]) -> str:
        """Register a new data source. Returns its unique ID."""
        reg = _load_registry()
        source_id = str(uuid.uuid4())
        reg[source_id] = {
            **config,
            "id": source_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_sync": None,
            "last_sync_status": None,
            "last_sync_rows": None,
        }
        _save_registry(reg)
        logger.info(f"Registered data source '{config.get('name')}' → {source_id}")
        return source_id

    def list_sources(self) -> List[Dict[str, Any]]:
        """Return all registered sources (passwords redacted)."""
        reg = _load_registry()
        safe = []
        for src in reg.values():
            s = {k: v for k, v in src.items() if k not in ("password", "api_key", "api_token")}
            safe.append(s)
        return safe

    def get(self, source_id: str) -> Dict[str, Any]:
        reg = _load_registry()
        if source_id not in reg:
            raise KeyError(f"Data source not found: {source_id}")
        return reg[source_id]

    def update(self, source_id: str, updates: Dict[str, Any]) -> None:
        reg = _load_registry()
        if source_id not in reg:
            raise KeyError(f"Data source not found: {source_id}")
        reg[source_id].update(updates)
        _save_registry(reg)

    def delete(self, source_id: str) -> None:
        reg = _load_registry()
        if source_id not in reg:
            raise KeyError(f"Data source not found: {source_id}")
        name = reg[source_id].get("name", source_id)
        del reg[source_id]
        _save_registry(reg)
        logger.info(f"Deleted data source '{name}'")

    def test(self, source_id: str) -> Tuple[bool, str]:
        """Test connectivity without pulling data. Returns (ok, message)."""
        cfg = self.get(source_id)
        src_type = cfg.get("type", "database")

        try:
            if src_type == "csv":
                path = Path(cfg["file_path"])
                if not path.exists():
                    return False, f"File not found: {path}"
                pd.read_csv(path, nrows=1)
                return True, f"CSV file accessible ({path})"

            elif src_type == "excel":
                path = Path(cfg["file_path"])
                if not path.exists():
                    return False, f"File not found: {path}"
                pd.read_excel(path, nrows=1)
                return True, f"Excel file accessible ({path})"

            elif src_type == "database":
                engine = _build_engine(cfg)
                with engine.connect() as conn:
                    from sqlalchemy import text
                    conn.execute(text("SELECT 1"))
                return True, f"Connected to {cfg.get('db_type')} @ {cfg.get('host')}"

            elif src_type == "rest_api":
                import requests
                base_url = cfg["api_url"].rstrip("/")
                headers = {}
                if cfg.get("api_key"):
                    headers["Authorization"] = f"Bearer {cfg['api_key']}"
                resp = requests.get(
                    f"{base_url}{cfg.get('health_endpoint', '/api/v1/courses')}",
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                return True, f"REST API reachable ({resp.status_code})"

            else:
                return False, f"Unknown source type: {src_type}"

        except Exception as exc:
            return False, str(exc)

    def fetch(self, source_id: str) -> pd.DataFrame:
        """Pull data from the source and return a normalised DataFrame."""
        cfg = self.get(source_id)
        src_type = cfg.get("type", "database")
        custom_map: Dict[str, str] = cfg.get("column_map", {})

        logger.info(f"Fetching from source '{cfg.get('name')}' (type={src_type})")

        if src_type == "csv":
            df = pd.read_csv(cfg["file_path"])

        elif src_type == "excel":
            sheet = cfg.get("sheet_name", 0)
            df = pd.read_excel(cfg["file_path"], sheet_name=sheet)

        elif src_type == "database":
            engine = _build_engine(cfg)
            query = cfg.get("query") or f"SELECT * FROM {cfg['table']}"
            df = pd.read_sql(query, engine)

        elif src_type == "rest_api":
            df = _fetch_rest_api(cfg)

        else:
            raise ValueError(f"Unknown source type: {src_type}")

        # Normalise column names
        df.columns = [c.lower().strip() for c in df.columns]
        df = _apply_column_map(df, custom_map)

        rows = len(df)
        logger.info(f"Fetched {rows} rows from '{cfg.get('name')}'")

        # Update sync metadata
        self.update(source_id, {
            "last_sync": datetime.utcnow().isoformat(),
            "last_sync_status": "success",
            "last_sync_rows": rows,
        })

        return df

    def sync_to_training_data(self, source_id: str) -> Dict[str, Any]:
        """
        Fetch from source, validate, and write to data/raw/students.csv
        so the ML pipeline can pick it up immediately.
        """
        from pipelines.etl_pipeline import DataValidator, DataCleaner

        df = self.fetch(source_id)
        validator = DataValidator()
        cleaner = DataCleaner()

        result = validator.validate(df)
        df_clean = cleaner.clean(df)

        out = Path("data/raw/students.csv")
        df_clean.to_csv(out, index=False)

        return {
            "rows_fetched": len(df),
            "rows_after_cleaning": len(df_clean),
            "output": str(out),
            "validation_errors": result.errors,
            "validation_warnings": result.warnings,
        }
