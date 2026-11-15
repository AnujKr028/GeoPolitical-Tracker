"""
seed.py
Sample data insert karta hai. Run:  python seed.py

IMPORTANT: ye sirf starter data hai. Dates/details apni taraf se verify karo
aur EVENTS list me apne 20-30 events aur add karo (target 40-50 total).
credibility_score subjective hai: report me batana ki tumne kaise decide kiya.
"""
from datetime import datetime
from db_setup import get_db, setup_database


def d(s):
    return datetime.strptime(s, "%Y-%m-%d")


ACTORS = [
    {"_id": "IND", "name": "India", "type": "state", "region": "South Asia", "aligned_with": ["RUS"]},
    {"_id": "PAK", "name": "Pakistan", "type": "state", "region": "South Asia", "aligned_with": ["CHN"]},
    {"_id": "NPL", "name": "Nepal", "type": "state", "region": "South Asia", "aligned_with": []},
    {"_id": "USA", "name": "United States", "type": "state", "region": "North America", "aligned_with": ["ISR", "UKR", "NATO"]},
    {"_id": "CHN", "name": "China", "type": "state", "region": "East Asia", "aligned_with": ["RUS", "PAK", "IRN"]},
    {"_id": "RUS", "name": "Russia", "type": "state", "region": "Europe", "aligned_with": ["IRN", "CHN"]},
    {"_id": "UKR", "name": "Ukraine", "type": "state", "region": "Europe", "aligned_with": ["USA", "EU", "NATO"]},
    {"_id": "ISR", "name": "Israel", "type": "state", "region": "Middle East", "aligned_with": ["USA"]},
    {"_id": "IRN", "name": "Iran", "type": "state", "region": "Middle East", "aligned_with": ["RUS", "CHN", "HAMAS"]},
    {"_id": "HAMAS", "name": "Hamas", "type": "non-state-group", "region": "Middle East", "aligned_with": ["IRN"]},
    {"_id": "EU", "name": "European Union", "type": "organization", "region": "Europe", "aligned_with": ["NATO", "UKR"]},
    {"_id": "NATO", "name": "NATO", "type": "organization", "region": "Europe", "aligned_with": ["USA", "EU", "UKR"]},
]

SOURCES = [
    {"_id": "reuters", "name": "Reuters", "credibility_score": 92, "country": "UK"},
    {"_id": "ap", "name": "Associated Press", "credibility_score": 92, "country": "USA"},
    {"_id": "bbc", "name": "BBC News", "credibility_score": 88, "country": "UK"},
    {"_id": "aljazeera", "name": "Al Jazeera", "credibility_score": 80, "country": "Qatar"},
    {"_id": "thehindu", "name": "The Hindu", "credibility_score": 82, "country": "India"},
    {"_id": "dawn", "name": "Dawn", "credibility_score": 78, "country": "Pakistan"},
]

RELATIONS = [
    {"actor_a": "USA", "actor_b": "ISR", "relation_type": "ally", "since": 1948},
    {"actor_a": "USA", "actor_b": "UKR", "relation_type": "ally", "since": 1992},
    {"actor_a": "USA", "actor_b": "NATO", "relation_type": "ally", "since": 1949},
    {"actor_a": "RUS", "actor_b": "IRN", "relation_type": "ally", "since": 2001},
    {"actor_a": "CHN", "actor_b": "PAK", "relation_type": "ally", "since": 1951},
    {"actor_a": "CHN", "actor_b": "RUS", "relation_type": "trade-partner", "since": 1991},
    {"actor_a": "IND", "actor_b": "RUS", "relation_type": "trade-partner", "since": 1947},
    {"actor_a": "IND", "actor_b": "PAK", "relation_type": "rival", "since": 1947},
    {"actor_a": "ISR", "actor_b": "IRN", "relation_type": "rival", "since": 1979},
    {"actor_a": "ISR", "actor_b": "HAMAS", "relation_type": "rival", "since": 1987},
    {"actor_a": "USA", "actor_b": "RUS", "relation_type": "sanction", "since": 2014},
    {"actor_a": "USA", "actor_b": "CHN", "relation_type": "rival", "since": 2018},
]


def ev(date, country, region, etype, sev, actors, src, summary, status="verified"):
    return {
        "date": d(date),
        "location": {"country": country, "region": region},
        "type": etype,
        "severity": sev,
        "actors_involved": actors,
        "source_id": src,
        "summary": summary,
        "status": status,
    }


EVENTS = [
    ev("2022-02-24", "Ukraine", "Europe", "conflict", 10, ["RUS", "UKR", "NATO"], "reuters", "Russia launches full-scale invasion of Ukraine."),
    ev("2023-10-07", "Israel", "Middle East", "conflict", 10, ["HAMAS", "ISR"], "ap", "Hamas attack on southern Israel begins the Gaza war."),
    ev("2025-02-28", "United States", "North America", "diplomacy", 4, ["USA", "UKR"], "bbc", "Tense Trump-Zelensky meeting at the White House."),
    ev("2025-04-02", "United States", "North America", "sanction", 6, ["USA", "CHN", "EU"], "reuters", "Sweeping new US tariffs announced on most trading partners."),
    ev("2025-04-10", "China", "East Asia", "sanction", 7, ["USA", "CHN"], "reuters", "US-China tariff escalation reaches triple digits."),
    ev("2025-04-22", "India", "South Asia", "conflict", 7, ["IND", "PAK"], "thehindu", "Terror attack in Pahalgam, Kashmir kills tourists."),
    ev("2025-05-07", "Pakistan", "South Asia", "conflict", 8, ["IND", "PAK"], "thehindu", "India strikes targets across the border (Operation Sindoor)."),
    ev("2025-05-10", "India", "South Asia", "diplomacy", 4, ["IND", "PAK", "USA"], "dawn", "India and Pakistan announce a ceasefire.", "reported"),
    ev("2025-05-12", "Switzerland", "Europe", "diplomacy", 3, ["USA", "CHN"], "reuters", "US and China agree to temporary tariff reduction in Geneva."),
    ev("2025-06-01", "Russia", "Europe", "conflict", 7, ["UKR", "RUS"], "bbc", "Ukraine drone operation hits Russian airbases."),
    ev("2025-06-13", "Iran", "Middle East", "conflict", 9, ["ISR", "IRN"], "reuters", "Israel strikes Iran; the 12-day war begins."),
    ev("2025-06-22", "Iran", "Middle East", "conflict", 9, ["USA", "IRN"], "ap", "US strikes Iranian nuclear facilities."),
    ev("2025-06-24", "Iran", "Middle East", "diplomacy", 5, ["ISR", "IRN", "USA"], "aljazeera", "Israel-Iran ceasefire takes effect."),
    ev("2025-08-06", "India", "South Asia", "sanction", 6, ["USA", "IND"], "thehindu", "US announces extra tariff on India over Russian oil purchases."),
    ev("2025-08-15", "United States", "North America", "diplomacy", 4, ["USA", "RUS"], "ap", "Trump-Putin summit in Alaska."),
    ev("2025-08-31", "China", "East Asia", "diplomacy", 2, ["CHN", "IND", "RUS"], "thehindu", "SCO summit in Tianjin; Modi, Xi and Putin attend."),
    ev("2025-09-03", "China", "East Asia", "diplomacy", 2, ["CHN", "RUS"], "bbc", "Beijing military parade with Putin in attendance."),
    ev("2025-09-09", "Nepal", "South Asia", "protest", 7, ["NPL"], "thehindu", "Youth-led protests; PM resigns amid unrest."),
    ev("2025-09-09", "Qatar", "Middle East", "conflict", 7, ["ISR", "HAMAS"], "aljazeera", "Israeli strike targets Hamas leaders in Doha."),
    ev("2025-09-10", "Poland", "Europe", "conflict", 6, ["RUS", "NATO"], "reuters", "Russian drones enter Polish airspace."),
    ev("2025-10-09", "Egypt", "Middle East", "diplomacy", 5, ["ISR", "HAMAS", "USA"], "ap", "First-phase Gaza ceasefire deal agreed."),
    ev("2025-10-22", "United States", "North America", "sanction", 6, ["USA", "RUS"], "reuters", "US sanctions major Russian oil companies."),
    ev("2025-10-30", "South Korea", "East Asia", "diplomacy", 3, ["USA", "CHN"], "bbc", "Trump-Xi meeting produces trade truce."),
]


def seed():
    db = get_db()
    setup_database(db)

    # data clear karo (validators bache rahenge)
    for name in ("events", "actors", "sources", "relations"):
        db[name].delete_many({})

    db.actors.insert_many(ACTORS)
    db.sources.insert_many(SOURCES)
    db.relations.insert_many(RELATIONS)
    db.events.insert_many(EVENTS)

    for name in ("actors", "sources", "relations", "events"):
        print(f"{name}: {db[name].count_documents({})} documents")


if __name__ == "__main__":
    seed()
