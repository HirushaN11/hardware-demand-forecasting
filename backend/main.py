import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Safe relative & root imports for advisor functions
try:
    from backend.advisor import (
        generate_inventory_brief,
        answer_copilot_chat,
        generate_clearance_recommendations,
    )
except ImportError:
    from advisor import (
        generate_inventory_brief,
        answer_copilot_chat,
        generate_clearance_recommendations,
    )

# -------------------------------------------------------------------
# FastAPI App Initialization & CORS Setup
# -------------------------------------------------------------------
app = FastAPI(
    title="Hardware Demand Forecasting & AI Copilot",
    description="Dynamic DSS and Supply Chain Copilot for Retail Hardware Stores",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Data Loading Utilities
# -------------------------------------------------------------------
# Resolve path to future_inventory_plan.csv dynamically
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_CANDIDATES = [
    BASE_DIR / "results" / "tables" / "future_inventory_plan.csv",
    BASE_DIR / "results" / "future_inventory_plan.csv",
    BASE_DIR / "data" / "future_inventory_plan.csv",
    Path("results/tables/future_inventory_plan.csv"),
    Path("results/future_inventory_plan.csv"),
    Path("future_inventory_plan.csv")
]

inventory_df = pd.DataFrame()

for p in DATA_CANDIDATES:
    if p.exists():
        try:
            inventory_df = pd.read_csv(p)
            print(f"INFO: Successfully loaded inventory dataset from {p} ({len(inventory_df)} records)")
            break
        except Exception as e:
            print(f"WARNING: Found dataset at {p} but failed to parse: {e}")

if inventory_df.empty:
    print("WARNING: future_inventory_plan.csv not found in standard directories. Initializing empty dataset.")


def get_current_records() -> List[Dict[str, Any]]:
    """Helper to return inventory records as a clean list of dictionaries."""
    if not inventory_df.empty:
        return inventory_df.to_dict(orient="records")
    return []


# -------------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------------
class CopilotChatRequest(BaseModel):
    query: str
    api_key: Optional[str] = None


class SkuBriefRequest(BaseModel):
    sku_data: Dict[str, Any]
    api_key: Optional[str] = None


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Hardware Demand Forecasting & AI Copilot API",
        "total_skus": len(inventory_df)
    }


@app.get("/api/inventory/recommendations")
def get_inventory_recommendations():
    """Returns inventory demand plan as a raw list for the React operational dashboard."""
    return get_current_records()


@app.get("/api/inventory")
def get_inventory():
    """Returns the full 30-SKU inventory demand plan with metadata."""
    records = get_current_records()
    return {
        "status": "success",
        "count": len(records),
        "data": records
    }


@app.post("/api/copilot")
@app.post("/api/advisor/chat")
def copilot_chat(payload: CopilotChatRequest):
    """
    Dynamic AI Supply Chain Copilot chat endpoint.
    Uses LLM reasoning over live inventory metrics to return strategic briefs and dynamic charts.
    """
    records = get_current_records()
    if not records:
        raise HTTPException(status_code=500, detail="Inventory dataset is not available.")

    result = answer_copilot_chat(
        user_query=payload.query,
        inventory_records=records,
        api_key=payload.api_key
    )
    return result


@app.post("/api/advisor/brief")
@app.post("/api/advisor/generate")
def get_sku_brief(payload: SkuBriefRequest):
    """Generates a concise procurement notice for an individual SKU."""
    brief_text = generate_inventory_brief(
        sku_data=payload.sku_data,
        api_key=payload.api_key
    )
    return {
        "status": "success",
        "brief": brief_text,
        "advice": brief_text
    }


@app.get("/api/recommendations")
def get_clearance_recommendations():
    """
    Identifies slow-moving or overstocked hardware SKUs and returns
    clearance markdown and cross-selling bundle recommendations.
    """
    try:
        records = get_current_records()
        if not records:
            return {"status": "error", "message": "No inventory records loaded.", "recommendations": []}

        recommendations = generate_clearance_recommendations(records)
        return {
            "status": "success",
            "count": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "recommendations": []
        }


# -------------------------------------------------------------------
# Local Runner
# -------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
