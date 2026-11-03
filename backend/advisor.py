import os
import json
from groq import Groq

# Candidate model IDs ordered by availability on Groq
CANDIDATE_MODELS = [
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b"
]


def clean_json_text(text: str) -> str:
    """Strips markdown code fences (```json ... ```) from LLM output."""
    t = text.strip()
    if t.startswith("```"):
        parts = t.split("\n", 1)
        t = parts[1] if len(parts) > 1 else ""
    if t.endswith("```"):
        t = t.rsplit("```", 1)[0]
    return t.strip()


def generate_inventory_brief(sku_data: dict, api_key: str = None) -> str:
    """
    Generates a single SKU procurement briefing using Groq with auto-fallback.
    """
    fallback_text = (
        f"Advisory Notice for {sku_data.get('product_name')} ({sku_data.get('sku_id')}): "
        f"Current stock is {sku_data.get('current_stock')} units against reorder threshold "
        f"{sku_data.get('reorder_point')}. Status: {sku_data.get('reorder_status')}."
    )

    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        return fallback_text

    client = Groq(api_key=key)
    prompt = f"""
You are a senior supply chain consultant for retail hardware stores in Sri Lanka.
Analyze this SKU's metrics and provide a concise, professional 3-sentence procurement briefing:
{json.dumps(sku_data, indent=2)}
"""

    for model_name in CANDIDATE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception:
            continue

    return fallback_text


def answer_copilot_chat(user_query: str, inventory_records: list, api_key: str = None) -> dict:
    """
    Dynamic generative AI reasoning over all 30 SKUs with automated model discovery.
    """
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        return {
            "text": "⚠️ **GROQ_API_KEY is missing.** Please set your Groq key in your .env file.",
            "chart": None
        }

    dataset_summary = []
    for r in inventory_records:
        dataset_summary.append({
            "sku": r.get("sku_id"),
            "name": r.get("product_name"),
            "category": r.get("category"),
            "stock": r.get("current_stock"),
            "rop": r.get("reorder_point"),
            "safety_stock": r.get("safety_stock"),
            "status": r.get("reorder_status"),
            "order_units": r.get("suggested_order_units"),
            "unit_cost_lkr": r.get("unit_cost_lkr"),
            "selling_price_lkr": r.get("selling_price_lkr"),
            "reorder_spend_lkr": r.get("capital_outlay_lkr"),
            "predicted_4w_demand": r.get("forecast_4w_total")
        })

    client = Groq(api_key=key)

    system_prompt = f"""
You are the AI Chief Supply Chain Copilot for a Sri Lankan retail hardware store.
You have access to live inventory and 4-week demand forecasts across 30 products:

LIVE CATALOG DATA:
{json.dumps(dataset_summary, indent=2)}

USER QUESTION:
"{user_query}"

INSTRUCTIONS:
1. Provide a direct, data-grounded, professional response tailored specifically to the user's question.
2. If the user's question asks for ranking, category details, budget splits, high demand, or comparisons, generate a `chart` object with 3 to 6 relevant items.
3. IN `chart.explanation`, clearly explain the specific business logic or supply chain reason (e.g. "Product X is prioritized first because...") for why the first product or category is at the top.
4. If no chart is applicable (e.g. general greetings), set "chart": null.
5. You MUST return ONLY a valid JSON object matching this schema:
{{
  "text": "Your complete written strategic response here...",
  "chart": {{
    "type": "bar",
    "title": "Chart Title Here",
    "explanation": "Clear explanation of why the top product is ranked first.",
    "labels": ["Item A", "Item B", "Item C"],
    "values": [25000, 18500, 9200]
  }}
}}
"""

    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": system_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            last_error = str(e)
            continue

    return {
        "text": f"Error running dynamic AI copilot: {last_error}",
        "chart": None
    }


def generate_clearance_recommendations(inventory_records: list, api_key: str = None) -> list:
    """
    Scans for overstocked / slow-moving SKUs and generates bundle or discount recommendations.
    """
    # 1. Identify slow-moving items: stock is at least 2.5x higher than 4-week forecast
    slow_items = []
    fast_items = []

    for r in inventory_records:
        stock = r.get("current_stock", 0)
        f4w = r.get("forecast_4w_total", 0)
        category = r.get("category", "")
        name = r.get("product_name", "")
        sku = r.get("sku_id", "")
        cost = r.get("unit_cost_lkr", 0)
        price = r.get("selling_price_lkr", 0)

        # Ratio calculation
        turnover_ratio = stock / (f4w if f4w > 0 else 0.5)

        item_dict = {
            "sku": sku,
            "name": name,
            "category": category,
            "stock": stock,
            "f4w": f4w,
            "unit_price": price,
            "turnover_ratio": turnover_ratio
        }

        if turnover_ratio >= 2.0 and stock > 10:
            slow_items.append(item_dict)
        elif turnover_ratio <= 1.2:
            fast_items.append(item_dict)

    if not slow_items:
        # Fallback to top 3 highest stock SKUs if ratio condition is empty
        sorted_by_stock = sorted(inventory_records, key=lambda x: x.get("current_stock", 0), reverse=True)
        slow_items = [{
            "sku": x.get("sku_id"),
            "name": x.get("product_name"),
            "category": x.get("category"),
            "stock": x.get("current_stock"),
            "f4w": x.get("forecast_4w_total"),
            "unit_price": x.get("selling_price_lkr"),
            "turnover_ratio": 2.5
        } for x in sorted_by_stock[:3]]

    fallback_recommendations = [
        {
            "slow_item": item["name"],
            "sku": item["sku"],
            "stock_on_hand": item["stock"],
            "forecast_demand": item["f4w"],
            "strategy_type": "Clearance Markdown",
            "strategy": "Volume Discount",
            "paired_with": None,
            "discount_pct": "15%",
            "reasoning": f"{item['name']} has low turnover ({item['stock']} in stock vs {round(item['f4w'])} expected 4-week sales). Offering a 15% markdown or cross-selling bundle unblocks working capital quickly."
        }
        for item in slow_items[:3]
    ]

    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        return fallback_recommendations

    client = Groq(api_key=key)

    prompt = f"""
You are a retail hardware merchandising expert in Sri Lanka.
Below are slow-moving SKUs with high inventory relative to expected demand, along with fast-moving SKUs:

SLOW-MOVING (OVERSTOCKED) ITEMS:
{json.dumps(slow_items[:5], indent=2)}

FAST-MOVING ITEMS:
{json.dumps(fast_items[:5], indent=2)}

Task:
Generate 3 to 4 actionable merchandising strategies for the slow-moving items.
For each item, recommend either:
1. "Bundle Promotion": Pair the slow item with a complementary fast-moving item (e.g., primer with topcoat, wire clips with conduit, or bolts with drill bits).
2. "Clearance Markdown": Offer an exact promotional discount (e.g., 10% - 20% off) to liquidate capital.

Return ONLY a valid JSON array matching this exact schema:
[
  {{
    "slow_item": "Product Name",
    "sku": "SKU_ID",
    "strategy_type": "Bundle Promotion" or "Clearance Markdown",
    "paired_with": "Complementary Fast-Moving Product Name (or 'None')",
    "discount_pct": "15%",
    "reasoning": "Clear explanation of why this product is moving slowly and how this bundle/discount unblocks working capital."
  }}
]
"""

    for model_name in CANDIDATE_MODELS:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            raw = res.choices[0].message.content
            cleaned = clean_json_text(raw)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception:
            continue

    return fallback_recommendations
