"""GSC API client with OAuth Desktop flow and parquet caching."""

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DATA_LAG_DAYS = 5
ROW_LIMIT = 25000

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data" / "gsc"


def get_credentials(token_path: Path | None = None, client_secret_path: Path | None = None) -> Credentials:
    """Load or create OAuth credentials."""
    token_path = token_path or CONFIG_DIR / "gsc_token.json"
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds, token_path)
    elif not creds or not creds.valid:
        if client_secret_path and client_secret_path.exists():
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=8090, open_browser=True)
        else:
            raise FileNotFoundError(
                f"No valid token at {token_path} and no client_secret file provided. "
                "Run `evo gsc auth --client-secret <path>` first."
            )
        _save_token(creds, token_path)

    return creds


def save_token_from_dict(token_data: dict, token_path: Path | None = None):
    """Save token data dict directly (for manual/Playwright-based auth)."""
    token_path = token_path or CONFIG_DIR / "gsc_token.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)


def _save_token(creds: Credentials, token_path: Path):
    """Persist credentials to JSON."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())


def build_service(creds: Credentials | None = None):
    """Build GSC API service."""
    if creds is None:
        creds = get_credentials()
    return build("searchconsole", "v1", credentials=creds)


def list_sites(service=None) -> list[str]:
    """List all verified sites in GSC."""
    if service is None:
        service = build_service()
    response = service.sites().list().execute()
    return [s["siteUrl"] for s in response.get("siteEntry", [])]


def query_day(service, site_url: str, query_date: date) -> pd.DataFrame:
    """Query GSC for a single day. Returns DataFrame with columns:
    query, page, device, country, position, clicks, impressions, ctr.
    """
    request_body = {
        "startDate": query_date.isoformat(),
        "endDate": query_date.isoformat(),
        "dimensions": ["query", "page", "device", "country"],
        "rowLimit": ROW_LIMIT,
        "startRow": 0,
    }

    all_rows = []
    while True:
        response = service.searchanalytics().query(
            siteUrl=site_url, body=request_body
        ).execute()

        rows = response.get("rows", [])
        if not rows:
            break

        for row in rows:
            keys = row["keys"]
            all_rows.append({
                "query": keys[0],
                "page": keys[1],
                "device": keys[2],
                "country": keys[3],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": row["ctr"],
                "position": row["position"],
                "date": query_date.isoformat(),
            })

        if len(rows) < ROW_LIMIT:
            break
        request_body["startRow"] += ROW_LIMIT

    if not all_rows:
        return pd.DataFrame()

    return pd.DataFrame(all_rows)


def _parquet_path(query_date: date) -> Path:
    """Get parquet file path for a date."""
    return DATA_DIR / f"{query_date.isoformat()}.parquet"


def _atomic_write_parquet(df: pd.DataFrame, path: Path):
    """Write parquet atomically: write to tmp, then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    os.close(tmp_fd)
    try:
        df.to_parquet(tmp_path, index=False)
        os.rename(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def sync(site_url: str, days: int = 90, service=None) -> dict:
    """Sync GSC data for the last N days. Returns sync stats."""
    if service is None:
        service = build_service()

    # Clean up any leftover .tmp files
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for tmp in DATA_DIR.glob("*.tmp"):
        tmp.unlink()

    today = date.today()
    end_date = today - timedelta(days=DATA_LAG_DAYS)
    start_date = end_date - timedelta(days=days)

    synced = 0
    skipped = 0
    empty = 0
    current = start_date

    while current <= end_date:
        parquet_path = _parquet_path(current)
        if parquet_path.exists():
            skipped += 1
        else:
            df = query_day(service, site_url, current)
            if df.empty:
                empty += 1
            else:
                _atomic_write_parquet(df, parquet_path)
                synced += 1
        current += timedelta(days=1)

    return {
        "site_url": site_url,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "synced": synced,
        "skipped": skipped,
        "empty": empty,
    }


def load_data(start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
    """Load cached parquet data into a single DataFrame."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.parquet"))

    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        file_date = date.fromisoformat(f.stem)
        if start_date and file_date < start_date:
            continue
        if end_date and file_date > end_date:
            continue
        dfs.append(pd.read_parquet(f))

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def status() -> dict:
    """Return sync status: date range, file count, total rows."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.parquet"))

    if not files:
        return {"files": 0, "rows": 0, "start_date": None, "end_date": None}

    total_rows = 0
    for f in files:
        df = pd.read_parquet(f)
        total_rows += len(df)

    return {
        "files": len(files),
        "rows": total_rows,
        "start_date": files[0].stem,
        "end_date": files[-1].stem,
    }
