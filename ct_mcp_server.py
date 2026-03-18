import httpx
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OpenFDA")

FDA_BASE_URL = "https://api.fda.gov"

HEADERS = {
    "User-Agent": "clinical-trials-agent/1.0",
    "Accept": "application/json"
}

@mcp.tool()
async def search_approvals(
    sponsor: str = None,
    drug_name: str = None,
    limit: int = 20
) -> str:
    """Search FDA drug approval records by sponsor or drug name.

    Args:
        sponsor: Company or sponsor name (e.g. 'Pfizer', 'Merck')
        drug_name: Drug or active ingredient name (e.g. 'pembrolizumab')
        limit: Number of results to return (default 20)
    """
    if sponsor:
        search = f'sponsor_name:"{sponsor}"'
    elif drug_name:
        search = f'products.brand_name:"{drug_name}"'
    else:
        return json.dumps({"error": "Provide either sponsor or drug_name"})

    params = {
        "search": search,
        "limit": limit
    }

    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(
            f"{FDA_BASE_URL}/drug/drugsfda.json",
            params=params,
            timeout=30.0
        )

    if response.status_code == 404:
        return json.dumps({"message": "No approvals found", "total": 0, "results": []})

    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("results", []):
        products = item.get("products", [{}])
        results.append({
            "application_number": item.get("application_number", ""),
            "sponsor": item.get("sponsor_name", ""),
            "brand_name": products[0].get("brand_name", "") if products else "",
            "generic_name": products[0].get("active_ingredients", [{}])[0].get("name", "") if products else "",
            "dosage_form": products[0].get("dosage_form", "") if products else "",
            "marketing_status": products[0].get("marketing_status", "") if products else "",
            "submissions": [
                {
                    "type": s.get("submission_type", ""),
                    "number": s.get("submission_number", ""),
                    "status": s.get("submission_status", ""),
                    "date": s.get("submission_status_date", "")
                }
                for s in item.get("submissions", [])[:3]
            ]
        })

    return json.dumps({
        "total": data.get("meta", {}).get("results", {}).get("total", 0),
        "returned": len(results),
        "results": results
    })


@mcp.tool()
async def search_adverse_events(
    drug_name: str,
    limit: int = 20
) -> str:
    """Search FDA adverse event reports for a drug.

    Args:
        drug_name: Drug name to search adverse events for (e.g. 'keytruda')
        limit: Number of results to return (default 20)
    """
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": limit
    }

    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(
            f"{FDA_BASE_URL}/drug/event.json",
            params=params,
            timeout=30.0
        )

    if response.status_code == 404:
        return json.dumps({"message": "No adverse events found", "drug": drug_name, "results": []})

    response.raise_for_status()
    data = response.json()

    results = [
        {"reaction": item.get("term", ""), "count": item.get("count", 0)}
        for item in data.get("results", [])
    ]

    return json.dumps({
        "drug": drug_name,
        "top_reactions": results
    })


@mcp.tool()
async def search_clinical_trials(
    drug_name: str = None,
    sponsor: str = None,
    limit: int = 10
) -> str:
    """Search FDA-submitted clinical trial results for a drug or sponsor.

    Args:
        drug_name: Drug name to search trials for (e.g. 'nivolumab')
        sponsor: Sponsor name to filter by (e.g. 'Bristol-Myers Squibb')
        limit: Number of results to return (default 10)
    """
    if drug_name:
        search = f'trade_name:"{drug_name}"'
    elif sponsor:
        search = f'sponsor_name:"{sponsor}"'
    else:
        return json.dumps({"error": "Provide either drug_name or sponsor"})

    params = {
        "search": search,
        "limit": limit
    }

    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(
            f"{FDA_BASE_URL}/drug/clinicaltrials.json",
            params=params,
            timeout=30.0
        )

    if response.status_code == 404:
        return json.dumps({"message": "No clinical trials found", "total": 0, "results": []})

    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "trade_name": item.get("trade_name", ""),
            "sponsor": item.get("sponsor_name", ""),
            "indication": item.get("indication", ""),
            "study_type": item.get("study_type", ""),
            "control_type": item.get("control_type", ""),
            "population": item.get("population", "")
        })

    return json.dumps({
        "total": data.get("meta", {}).get("results", {}).get("total", 0),
        "returned": len(results),
        "results": results
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")