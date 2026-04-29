"""
/api/v1/datasource  –  Data Source Management Router

Endpoints
---------
GET    /api/v1/datasource/             list all registered sources
POST   /api/v1/datasource/             register a new source
GET    /api/v1/datasource/types        list supported source types + required fields
GET    /api/v1/datasource/{id}         get one source (password redacted)
PUT    /api/v1/datasource/{id}         update a source
DELETE /api/v1/datasource/{id}         remove a source
POST   /api/v1/datasource/{id}/test    test connectivity
POST   /api/v1/datasource/{id}/sync    pull data → data/raw/students.csv
POST   /api/v1/datasource/{id}/preview pull first N rows (default 10)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.datasource.connector import DataSourceConnector

router = APIRouter(prefix="/api/v1/datasource", tags=["Data Sources"])
_connector = DataSourceConnector()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class DatabaseSourceConfig(BaseModel):
    """Config for a SQL database source."""
    name: str = Field(..., description="Human-readable label, e.g. 'Banner SIS'")
    type: str = Field("database", description="Must be 'database'")
    db_type: str = Field(..., description="postgresql | mysql | mssql | oracle | sqlite")
    host: Optional[str] = Field(None, description="DB host (not needed for sqlite)")
    port: Optional[int] = Field(None, description="DB port (uses default if omitted)")
    database: Optional[str] = Field(None, description="Database / schema name")
    username: Optional[str] = None
    password: Optional[str] = None
    query: Optional[str] = Field(
        None,
        description="Full SQL query. If omitted, 'table' must be set.",
        example="SELECT * FROM student_academic_view WHERE term = 'FALL2025'",
    )
    table: Optional[str] = Field(None, description="Table name (used when query is empty)")
    sqlite_path: Optional[str] = Field(None, description="Path to .db file (sqlite only)")
    column_map: Dict[str, str] = Field(
        default_factory=dict,
        description="Map source column names → internal names. Merged with defaults.",
        example={"cumulative_gpa": "gpa", "attend_pct": "attendance_rate"},
    )


class CsvSourceConfig(BaseModel):
    """Config for a CSV or Excel file source."""
    name: str
    type: str = Field(..., description="csv | excel")
    file_path: str = Field(..., description="Absolute or relative path to the file")
    sheet_name: Optional[str] = Field(None, description="Sheet name (Excel only)")
    column_map: Dict[str, str] = Field(default_factory=dict)


class RestApiSourceConfig(BaseModel):
    """Config for a REST API source (Canvas, Moodle, Blackboard, custom)."""
    name: str
    type: str = Field("rest_api", description="Must be 'rest_api'")
    api_url: str = Field(..., description="Base URL, e.g. https://canvas.university.edu")
    endpoint: str = Field(
        "/api/v1/students",
        description="Path to the student data endpoint",
    )
    health_endpoint: str = Field(
        "/api/v1/courses",
        description="Lightweight endpoint used for connectivity test",
    )
    api_key: Optional[str] = Field(None, description="Bearer token / API key")
    api_token: Optional[str] = Field(None, description="Alternative token field")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra query params appended to every request",
    )
    column_map: Dict[str, str] = Field(default_factory=dict)


class SourceUpdateRequest(BaseModel):
    """Partial update – only supplied fields are changed."""
    name: Optional[str] = None
    query: Optional[str] = None
    table: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    column_map: Optional[Dict[str, str]] = None


class PreviewRequest(BaseModel):
    rows: int = Field(10, ge=1, le=200, description="Number of rows to return")


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_source(src: Dict[str, Any]) -> Dict[str, Any]:
    """Strip secrets before returning to the client."""
    return {k: v for k, v in src.items() if k not in ("password", "api_key", "api_token")}


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("/types", summary="List supported source types and required fields")
def list_source_types():
    """
    Returns the supported source types with the fields required for each,
    so a UI can render the correct form dynamically.
    """
    return {
        "types": [
            {
                "type": "database",
                "label": "SQL Database",
                "description": "Connect to PostgreSQL, MySQL, MSSQL, Oracle, or SQLite",
                "supported_db_types": ["postgresql", "mysql", "mariadb", "mssql", "oracle", "sqlite"],
                "required_fields": ["name", "type", "db_type"],
                "optional_fields": ["host", "port", "database", "username", "password", "query", "table", "sqlite_path", "column_map"],
                "examples": {
                    "postgresql": {
                        "name": "Banner SIS",
                        "type": "database",
                        "db_type": "postgresql",
                        "host": "db.university.edu",
                        "port": 5432,
                        "database": "sis_prod",
                        "username": "readonly_user",
                        "password": "secret",
                        "query": "SELECT * FROM student_academic_view WHERE term = 'FALL2025'",
                    },
                    "sqlite": {
                        "name": "Local Dev DB",
                        "type": "database",
                        "db_type": "sqlite",
                        "sqlite_path": "data/university.db",
                        "table": "students",
                    },
                },
            },
            {
                "type": "csv",
                "label": "CSV File",
                "description": "Load student data from a CSV export",
                "required_fields": ["name", "type", "file_path"],
                "optional_fields": ["column_map"],
                "example": {
                    "name": "SIS Export",
                    "type": "csv",
                    "file_path": "data/raw/sis_export_fall2025.csv",
                },
            },
            {
                "type": "excel",
                "label": "Excel File",
                "description": "Load student data from an Excel workbook",
                "required_fields": ["name", "type", "file_path"],
                "optional_fields": ["sheet_name", "column_map"],
                "example": {
                    "name": "Registrar Export",
                    "type": "excel",
                    "file_path": "data/raw/students.xlsx",
                    "sheet_name": "Fall 2025",
                },
            },
            {
                "type": "rest_api",
                "label": "REST API",
                "description": "Connect to Canvas LMS, Moodle, Blackboard, or any REST API",
                "required_fields": ["name", "type", "api_url"],
                "optional_fields": ["endpoint", "health_endpoint", "api_key", "api_token", "params", "column_map"],
                "examples": {
                    "canvas": {
                        "name": "Canvas LMS",
                        "type": "rest_api",
                        "api_url": "https://canvas.university.edu",
                        "endpoint": "/api/v1/courses/123/students",
                        "api_key": "your_canvas_token",
                    },
                    "moodle": {
                        "name": "Moodle LMS",
                        "type": "rest_api",
                        "api_url": "https://moodle.university.edu",
                        "endpoint": "/webservice/rest/server.php",
                        "api_key": "your_moodle_token",
                        "params": {"wsfunction": "core_enrol_get_enrolled_users", "moodlewsrestformat": "json"},
                    },
                },
            },
        ],
        "column_map_defaults": {
            "note": "These source→internal mappings are applied automatically. Add extras via column_map.",
            "examples": {
                "cumulative_gpa": "gpa",
                "attend_pct": "attendance_rate",
                "final_grade": "exam_scores",
                "login_count": "lms_login_frequency",
                "discussion_posts": "forum_posts",
            },
        },
    }


@router.get("/", summary="List all registered data sources")
def list_sources():
    sources = _connector.list_sources()
    return {"count": len(sources), "sources": sources}


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new data source")
def register_source(config: Dict[str, Any]):
    """
    Register any supported source type. Pass the full config object.
    See `GET /api/v1/datasource/types` for required fields per type.
    """
    if "name" not in config:
        raise HTTPException(status_code=400, detail="'name' is required")
    if "type" not in config:
        raise HTTPException(status_code=400, detail="'type' is required (database | csv | excel | rest_api)")

    source_id = _connector.register(config)
    return {
        "message": "Data source registered successfully",
        "id": source_id,
        "name": config["name"],
        "type": config["type"],
    }


@router.get("/{source_id}", summary="Get a registered data source")
def get_source(source_id: str):
    try:
        src = _connector.get(source_id)
        return _safe_source(src)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")


@router.put("/{source_id}", summary="Update a data source")
def update_source(source_id: str, updates: SourceUpdateRequest):
    try:
        _connector.update(source_id, updates.model_dump(exclude_none=True))
        return {"message": "Updated successfully", "id": source_id}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a data source")
def delete_source(source_id: str):
    try:
        _connector.delete(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")


@router.post("/{source_id}/test", summary="Test connectivity to a data source")
def test_source(source_id: str):
    """
    Attempts a lightweight connection without pulling data.
    Returns `{"ok": true/false, "message": "..."}`.
    """
    try:
        _connector.get(source_id)  # raises if not found
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    ok, message = _connector.test(source_id)
    return {
        "ok": ok,
        "message": message,
        "source_id": source_id,
    }


@router.post("/{source_id}/preview", summary="Preview first N rows from a data source")
def preview_source(source_id: str, body: PreviewRequest = PreviewRequest()):
    """
    Fetches a small sample from the source so you can verify column mapping
    before running a full sync.
    """
    try:
        _connector.get(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    try:
        df = _connector.fetch(source_id)
        sample = df.head(body.rows)
        return {
            "source_id": source_id,
            "rows_returned": len(sample),
            "total_rows": len(df),
            "columns": list(sample.columns),
            "data": sample.fillna("").to_dict(orient="records"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{source_id}/sync", summary="Sync data source → data/raw/students.csv")
def sync_source(source_id: str):
    """
    Pulls all data from the source, runs it through the ETL validation
    and cleaning pipeline, then writes it to `data/raw/students.csv`.

    After a successful sync you can retrain the model immediately:
    ```
    POST /api/v1/predictions/retrain
    ```
    """
    try:
        _connector.get(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    try:
        result = _connector.sync_to_training_data(source_id)
        return {
            "message": "Sync completed successfully",
            "source_id": source_id,
            **result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
