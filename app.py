import os
from flask import Flask, render_template, request, jsonify
import cohere
from db_setup import get_db
from crud import get_events
from pipelines import country_severity_stats, monthly_escalation_trend
from ml_model import get_ml_conflict_clusters
from dotenv import load_dotenv

app = Flask(__name__)
db = get_db()

load_dotenv()


# Initialize cohere Client (Aap apni API key yahan daal sakte hain)
import cohere


COHERE_API_KEY = os.getenv("COHERE_API_KEY")


# Initialize Cohere Client with API Key

if not COHERE_API_KEY:
    raise RuntimeError("COHERE_API_KEY is missing!")


co = cohere.ClientV2(
    api_key=COHERE_API_KEY
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/country")
def country_page():
    return render_template("country.html")

@app.route("/api/dashboard-data")
def dashboard_data():
    # (Purana code wahi rahega)
    country = request.args.get("country")
    min_sev = int(request.args.get("min_sev", 1))
    if country == "All" or not country:
        country = None

    events = get_events(db, country=country, min_sev=min_sev, limit=50)
    formatted_events = [{"date": e["date"].strftime("%Y-%m-%d"), "country": e["location"]["country"], "region": e["location"].get("region", ""), "type": e["type"], "severity": e["severity"], "summary": e.get("summary", "")} for e in events]

    total_events = db.events.count_documents({})
    avg_sev = round(sum(e["severity"] for e in events) / len(events), 1) if events else 0
    countries = ["All"] + sorted(db.events.distinct("location.country"))

    return jsonify({
        "metrics": {"total_events": total_events, "filtered_count": len(formatted_events), "avg_severity": avg_sev},
        "countries": countries,
        "country_stats": country_severity_stats(db)[:12],
        "monthly_trend": monthly_escalation_trend(db),
        "ml_clusters": get_ml_conflict_clusters(db).head(15).to_dict(orient="records") if get_ml_conflict_clusters(db) is not None else [],
        "events": formatted_events,
    })

@app.route("/api/country-analysis")
def country_analysis():
    target_country = request.args.get("country", "India")
    
    # Database se saari unique countries ki list nikal lein
    countries = sorted(db.events.distinct("location.country"))

    # 1. Monthly Trend by Event Type
    trend_pipeline = [
        {"$match": {"location.country": target_country}},
        {
            "$group": {
                "_id": {
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}},
                    "type": "$type"
                },
                "count": {"$sum": 1},
                "avg_sev": {"$avg": "$severity"}
            }
        },
        {"$sort": {"_id.month": 1}}
    ]
    raw_trend = list(db.events.aggregate(trend_pipeline))

    # 2. Event Type Distribution
    type_pipeline = [
        {"$match": {"location.country": target_country}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}, "avg_sev": {"$avg": "$severity"}}},
        {"$sort": {"count": -1}}
    ]
    type_stats = list(db.events.aggregate(type_pipeline))

    # 3. Top Affected Regions/States
    region_pipeline = [
        {"$match": {"location.country": target_country}},
        {"$group": {"_id": "$location.region", "count": {"$sum": 1}, "max_sev": {"$max": "$severity"}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    region_stats = list(db.events.aggregate(region_pipeline))

    return jsonify({
        "selected_country": target_country,
        "countries": countries,  # <-- Yeh list ab frontend par jayegi
        "monthly_by_type": raw_trend,
        "type_stats": type_stats,
        "region_stats": region_stats
    })

# --- NEW: AI INSIGHTS API ENDPOINT ---

# --- COHERE AI INSIGHTS API ENDPOINT ---

@app.route("/api/ai-insights", methods=["POST"])
def ai_insights():
    data = request.get_json() or {}
    selected_country = data.get("country", "Global")

    # Get sample events from MongoDB
    country_filter = None if selected_country in ["All", "Global"] else selected_country

    sample_events = get_events(
        db,
        country=country_filter,
        limit=10
    )

    event_summaries = []

    for e in sample_events:
        date_str = (
            e['date'].strftime('%Y-%m-%d')
            if hasattr(e['date'], 'strftime')
            else str(e['date'])
        )

        event_country = e.get('location', {}).get('country', 'Unknown')
        summary_text = e.get('summary', '')

        event_summaries.append(
            f"- [{date_str}] {event_country}: "
            f"{e['type']} (Severity: {e['severity']}) - {summary_text}"
        )

    prompt = f"""

You are a Senior Geopolitical Intelligence Analyst working with
an international conflict monitoring and strategic research
organization.

Your task is to produce a comprehensive, evidence-based
Geopolitical Intelligence Report using the supplied ACLED
(Armed Conflict Location & Event Data) records.


Your analysis must be detailed, objective, analytical,
and suitable for presentation to policymakers, researchers,
security analysts, and international affairs professionals.

STRUCTURE YOUR REPORT INTO THE FOLLOWING SECTIONS:

1. EXECUTIVE INTELLIGENCE SUMMARY

Provide a concise overview of the geopolitical situation.
Highlight the most important developments, dominant event
categories, observed intensity, and overall patterns.
Identify the most significant findings that deserve attention.

2. CONFLICT TRENDS AND REGIONAL RISK ASSESSMENT

Examine the nature and frequency of recorded incidents.
Identify dominant forms of conflict, protests, political
violence, or other developments.

Discuss:
- Recurring patterns and notable concentrations of events.
- Whether recorded incidents indicate escalation,
  de-escalation, or no clear directional change.
- The geographical distribution of reported incidents,
  where location information is available.
- Potential implications for regional stability and security.

3. GEOPOLITICAL FACTORS AND UNDERLYING DRIVERS

Analyze possible factors that could explain the observed
events, including:
- Domestic political tensions and governance challenges.
- Socioeconomic inequalities and public grievances.
- Ethnic, religious, territorial, or regional disputes,
  where supported by evidence.
- International relations and cross-border tensions.
- Resource competition and economic pressures.
- Institutional and security-related developments.

Clearly distinguish documented evidence from hypotheses.
Do not present possible explanations as established facts.

4. EVENT SEVERITY AND VIOLENCE PATTERNS

Examine the severity distribution and intensity of events.

Discuss:
- Frequency of low, moderate, and high-severity incidents,
  if sufficient severity data is available.
- Whether specific event categories show higher severity.
- Notable changes or unusual severity patterns.
- Potential indicators of increasing instability.
- Differences between peaceful demonstrations,
  intervention-related protests, and violent incidents.

5. KEY GEOGRAPHICAL AND EVENT-BASED HOTSPOTS

Identify important locations, regions, or states associated
with recorded incidents.

Highlight:
- Areas with recurring incidents.
- Regions showing comparatively high severity.
- Dominant event categories in different locations.
- Potential geographical patterns requiring further
  investigation.

Only identify hotspots when supported by the supplied data.

6. POLITICAL, ECONOMIC AND HUMANITARIAN IMPLICATIONS

Discuss the possible consequences of observed developments
for:
- Political stability and governance.
- Public security and institutional trust.
- Economic activity and investment confidence.
- Civilian safety and social cohesion.
- Regional diplomatic and international relations.

Avoid overstating consequences that cannot be established
from the available records.

7. FUTURE OUTLOOK AND POTENTIAL SCENARIOS

Develop three analytical scenarios:

A. Baseline Scenario:
What may happen if currently observed patterns continue?

B. Escalation Scenario:
What developments could contribute to increasing tensions
or a deterioration in regional stability?

C. De-escalation Scenario:
What conditions or developments could support reduced
tensions and improved stability?

For each scenario, identify relevant indicators to monitor.
These are conditional scenarios, not predictions or
statistically calculated probabilities.

8. STRATEGIC WARNING INDICATORS

Identify important developments that analysts should monitor,
such as:
- Increasing frequency of violent incidents.
- Rising event severity.
- Geographic expansion of conflict.
- Repeated clashes or organized mobilization.
- Changes in government or security responses.
- Emergence of new event categories or actors.

Explain why each indicator matters.

9. FINAL INTELLIGENCE ASSESSMENT

Conclude with:
- The most important findings.
- The current situation supported by the data.
- Major uncertainties and information gaps.
- Issues requiring continued monitoring.

ANALYTICAL AND REPORTING GUIDELINES:

1. Base factual conclusions strictly on the supplied dataset.
2. Never invent events, statistics, locations, actors,
   casualties, political developments, or historical context.
3. Clearly distinguish recorded facts, analytical
   interpretations, and hypothetical scenarios.
4. Do not claim that a trend exists based on insufficient
   observations.
5. Do not assume that a small event sample represents
   the entire country's geopolitical situation.
6. If information is insufficient, explicitly acknowledge
   the limitation instead of generating speculation.
7. Do not confuse event frequency with event severity.
8. Use precise geopolitical terminology and professional
   intelligence-report language.
9. Avoid sensationalism, political bias, and unsupported
   conclusions.
10. Do not assign arbitrary numerical risk scores or
    probabilities.

FORMATTING REQUIREMENTS:

- Use a professional report-style structure.
- Use clear section headings and meaningful subheadings.
- Use numbered lists and bullet points where appropriate.
- Highlight important findings using bold text.
- Write detailed but readable paragraphs.
- Avoid unnecessary repetition and generic statements.
- Do not use tables unless they genuinely improve clarity.
- Do not include code, JSON, or technical explanations.

The final report should read like a professional geopolitical
intelligence briefing, combining data-driven observations,
careful interpretation, strategic context, and forward-looking
analysis.



WRITING STYLE AND REPORT PRESENTATION:

1. Write in a continuous, professional intelligence-report
   style rather than producing disconnected one-line statements.

2. Each major section should contain 1-3 substantial,
   well-developed paragraphs.

3. Each paragraph should generally contain 3-5 connected
   sentences explaining one analytical idea.

4. Connect related observations into cohesive paragraphs
   instead of placing every observation on a separate line.

5. Use bullet points only for genuinely distinct findings,
   indicators, or recommendations.

6. Limit each section to a maximum of 3-4 bullet points
   wherever possible.

7. Avoid excessive blank lines between paragraphs,
   headings, and list items.

8. Use clear and descriptive section headings, but do not
   create a new heading for every individual observation.

9. Maintain logical transitions between sections so that
   the report reads as one connected intelligence assessment.

10. Avoid repetitive introductory sentences and generic
    conclusions.

11. Prioritize analytical depth, factual precision,
    and meaningful interpretation over unnecessary length.

12. Do not artificially shorten paragraphs into one-line
    statements.

The final output must resemble a professionally written
geopolitical intelligence briefing, not a collection
of isolated AI-generated bullet points.

 
    """

    prompt += f"""

TARGET COUNTRY:
{selected_country}

ACTUAL ACLED EVENTS FROM MONGODB:

{chr(10).join(event_summaries)}

IMPORTANT:
Base your analysis on the above supplied events.
If the sample is insufficient, explicitly mention the limitation.
Do not invent statistics or events.
"""

    try:
        response = co.chat(
            model="command-a-03-2025",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        insight = response.message.content[0].text

        return jsonify({
            "status": "success",
            "insight": insight
        })

    except Exception as e:
        app.logger.exception("Cohere AI request failed")

        return jsonify({
            "status": "error",
            "message": "AI analysis failed. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)



print("Cohere API Key Loaded:", bool(os.getenv("COHERE_API_KEY")))