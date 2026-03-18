import json
import asyncio
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import anthropic
import os
from ct_mcp_server import search_approvals, search_adverse_events, search_clinical_trials

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "search_approvals",
        "description": "Search FDA drug approval records by sponsor or drug name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sponsor": {"type": "string", "description": "Company or sponsor name e.g. Pfizer Inc."},
                "drug_name": {"type": "string", "description": "Drug or brand name e.g. keytruda"},
                "limit": {"type": "integer", "description": "Number of results", "default": 20}
            }
        }
    },
    {
        "name": "search_adverse_events",
        "description": "Search FDA adverse event reports for a drug.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug name e.g. keytruda"},
                "limit": {"type": "integer", "description": "Number of results", "default": 20}
            },
            "required": ["drug_name"]
        }
    },
    {
        "name": "search_clinical_trials",
        "description": "Search FDA-submitted clinical trial results for a drug or sponsor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug name e.g. nivolumab"},
                "sponsor": {"type": "string", "description": "Sponsor name e.g. Merck"},
                "limit": {"type": "integer", "description": "Number of results", "default": 10}
            }
        }
    }
]

async def run_tool(name, inputs):
    if name == "search_approvals":
        return await search_approvals(**inputs)
    elif name == "search_adverse_events":
        return await search_adverse_events(**inputs)
    elif name == "search_clinical_trials":
        return await search_clinical_trials(**inputs)
    return json.dumps({"error": "Unknown tool"})

def run_agent(query):
    messages = [{"role": "user", "content": query}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system="""You are a pharmaceutical competitive intelligence analyst.
When given a drug name or sponsor, use the available tools to gather FDA approval records,
clinical trial results, and adverse event data. Then provide a structured competitive
intelligence summary with these exact sections:
1. Approval Overview
2. Clinical Trial Insights
3. Safety Profile
4. Competitive Takeaways

Use those exact section headings. Under each heading write 3-5 concise bullet points.
Be analytical and specific. Use the data returned by tools to support your points.""",
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = asyncio.run(run_tool(block.name, block.input))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            for block in response.content:
                if hasattr(block, "text"):
                    result = block.text
                    print("=== CLAUDE RESPONSE ===")
                    print(result)
                    print("=== END RESPONSE ===")
                    return result
            return "No response generated"

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FDA Competitive Intelligence Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Source Sans 3', sans-serif;
            background: #f0f4f8;
            color: #2d3748;
            min-height: 100vh;
        }

        header {
            background: #1a3c5e;
            color: white;
            padding: 22px 40px;
            border-bottom: 3px solid #e8a020;
        }

        header h1 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 24px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }

        .container {
            max-width: 980px;
            margin: 36px auto;
            padding: 0 24px;
        }

        .search-card {
            background: white;
            border-radius: 12px;
            padding: 24px 28px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            margin-bottom: 28px;
            border: 1px solid #e2e8f0;
        }

        .search-card label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: #718096;
            margin-bottom: 10px;
        }

        .search-row { display: flex; gap: 12px; }

        input[type="text"] {
            flex: 1;
            padding: 13px 18px;
            border: 1.5px solid #cbd5e0;
            border-radius: 8px;
            font-size: 15px;
            font-family: 'Source Sans 3', sans-serif;
            outline: none;
            transition: border-color 0.2s;
            color: #2d3748;
        }

        input[type="text"]:focus { border-color: #1a3c5e; }

        button {
            background: #1a3c5e;
            color: white;
            border: none;
            padding: 13px 28px;
            border-radius: 8px;
            font-size: 15px;
            font-family: 'Source Sans 3', sans-serif;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            white-space: nowrap;
        }

        button:hover { background: #245080; }
        button:disabled { background: #a0aec0; cursor: not-allowed; }

        .examples {
            margin-top: 10px;
            font-size: 13px;
            color: #a0aec0;
        }

        .examples span {
            cursor: pointer;
            color: #1a3c5e;
            margin-right: 14px;
            font-weight: 500;
            border-bottom: 1px dashed #1a3c5e;
            padding-bottom: 1px;
        }

        .examples span:hover { color: #e8a020; border-color: #e8a020; }

        .loading { text-align: center; padding: 48px; display: none; }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #e2e8f0;
            border-top-color: #1a3c5e;
            border-radius: 50%;
            animation: spin 0.75s linear infinite;
            margin: 0 auto 14px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }
        .loading p { color: #a0aec0; font-size: 14px; letter-spacing: 0.3px; }

        .error {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 16px 20px;
            color: #c53030;
            font-size: 14px;
            display: none;
            margin-bottom: 20px;
        }

        .results-header {
            display: none;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 2px solid #e2e8f0;
        }

        .results-header h2 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 22px;
            color: #1a3c5e;
        }

        .results-header p {
            font-size: 13px;
            color: #a0aec0;
            margin-top: 4px;
        }

        #resultsFull {
            display: none;
            background: white;
            border-radius: 12px;
            padding: 28px 32px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
            font-size: 14px;
            line-height: 1.8;
            color: #4a5568;
        }

        #resultsFull h3 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 17px;
            color: #1a3c5e;
            margin: 28px 0 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid #e2e8f0;
        }

        #resultsFull h3:first-child { margin-top: 0; }

        #resultsFull h4 {
            font-size: 14px;
            font-weight: 600;
            color: #2d3748;
            margin: 16px 0 6px;
        }

        #resultsFull ul {
            padding-left: 20px;
            margin: 6px 0 14px;
        }

        #resultsFull li { margin-bottom: 7px; }

        #resultsFull strong { color: #2d3748; }

        #resultsFull hr {
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 22px 0;
        }

        #resultsFull blockquote {
            background: #f7fafc;
            border-left: 3px solid #e8a020;
            padding: 10px 16px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
            color: #718096;
            margin: 16px 0;
        }

        #resultsFull p {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <header>
        <h1>FDA Competitive Intelligence Dashboard</h1>
    </header>

    <div class="container">
        <div class="search-card">
            <label>Search by drug name or sponsor</label>
            <div class="search-row">
                <input type="text" id="query" placeholder="e.g. keytruda, Pfizer Inc., nivolumab..." />
                <button id="searchBtn" onclick="runSearch()">Analyze</button>
            </div>
            <div class="examples">
                Try:
                <span onclick="setQuery('keytruda')">keytruda</span>
                <span onclick="setQuery('Pfizer Inc.')">Pfizer Inc.</span>
                <span onclick="setQuery('nivolumab')">nivolumab</span>
                <span onclick="setQuery('Merck')">Merck</span>
            </div>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Querying FDA data and generating analysis...</p>
        </div>

        <div class="error" id="error"></div>

        <div class="results-header" id="resultsHeader">
            <h2 id="resultsTitle">Analysis Results</h2>
            <p id="resultsSubtitle"></p>
        </div>

        <div id="resultsFull"></div>
    </div>

    <script>
        function setQuery(val) {
            document.getElementById('query').value = val;
        }

        function markdownToHtml(text) {
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/^---$/gm, '<hr>')
                .replace(/^#{1,2} ?\d*\.? ?(.+)$/gm, '<h3>$1</h3>')
                .replace(/^### ?(.+)$/gm, '<h4>$1</h4>')
                .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
                .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
                .replace(/(<li>[\s\S]*?<\/li>)(?=\s*<li>|\s*<h|$)/g, (match) => '<ul>' + match + '</ul>')
                .replace(/\n{2,}/g, '\n')
                .replace(/^(?!<[a-z]).+$/gm, (line) => line.trim() ? '<p>' + line + '</p>' : '')
                .replace(/\n/g, '');
        }

        async function runSearch() {
            const query = document.getElementById('query').value.trim();
            if (!query) return;

            document.getElementById('loading').style.display = 'block';
            document.getElementById('resultsFull').style.display = 'none';
            document.getElementById('resultsHeader').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('searchBtn').disabled = true;

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });

                const data = await response.json();

                if (data.error) {
                    document.getElementById('error').textContent = data.error;
                    document.getElementById('error').style.display = 'block';
                } else {
                    document.getElementById('resultsFull').innerHTML = markdownToHtml(data.result);
                    document.getElementById('resultsTitle').textContent = 'Analysis: ' + query;
                    document.getElementById('resultsSubtitle').textContent = 'Based on FDA approval records, clinical trial submissions, and adverse event reports';
                    document.getElementById('resultsHeader').style.display = 'block';
                    document.getElementById('resultsFull').style.display = 'block';
                }
            } catch (err) {
                document.getElementById('error').textContent = 'Something went wrong. Make sure the server is running.';
                document.getElementById('error').style.display = 'block';
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('searchBtn').disabled = false;
            }
        }

        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') runSearch();
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "No query provided"})
    try:
        result = run_agent(query)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)