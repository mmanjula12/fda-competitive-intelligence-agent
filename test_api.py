import httpx

url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "non-small cell lung cancer",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 5,
    "format": "json"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

response = httpx.get(url, params=params, headers=headers, timeout=30.0)
print(f"Status code: {response.status_code}")
print(response.text[:500])