import asyncio
import json
from ct_mcp_server import search_approvals, search_adverse_events, search_clinical_trials

async def test():
    print("=== Testing search_approvals for Pfizer ===")
    result = await search_approvals(sponsor="Pfizer Inc.")
    data = json.loads(result)
    print(f"Total approvals found: {data.get('total', 0)}")
    if data.get("results"):
        first = data["results"][0]
        print(f"First result: {first['brand_name']} ({first['generic_name']})")
        print(f"Sponsor: {first['sponsor']}")
        print(f"Application: {first['application_number']}")
    else:
        print("No results returned")

    print("\n=== Testing search_adverse_events for keytruda ===")
    result = await search_adverse_events(drug_name="keytruda")
    data = json.loads(result)
    if data.get("top_reactions"):
        print("Top 3 adverse reactions:")
        for r in data["top_reactions"][:3]:
            print(f"  {r['reaction']}: {r['count']} reports")

    print("\n=== Testing search_clinical_trials for pembrolizumab ===")
    result = await search_clinical_trials(sponsor="Merck")
    data = json.loads(result)
    print(f"Total trials found: {data.get('total', 0)}")
    if data.get("results"):
        first = data["results"][0]
        print(f"First result: {first['trade_name']} — {first['indication']}")
    else:
        print("No results returned")

asyncio.run(test())