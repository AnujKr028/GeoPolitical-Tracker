import pandas as pd
from datetime import datetime
from db_setup import get_db

db = get_db()

# Apni CSV file ka naam (jo aapne folder mein rakha hai)
csv_file = "ACLED Data_2026-11-13_event_date_from_2025-11-08_event_date_to_2026-11-06.csv"  # Agar aapne rename nahi kiya toh pura naam likhein

print("Reading CSV file...")
df = pd.read_csv(csv_file)

# ACLED event types ko hamare schema ke valid enum values mein map karna
def map_event_type(acled_type):
    t = str(acled_type).lower()
    if "protest" in t or "riot" in t:
        return "protest"
    elif "strategic" in t or "agreement" in t:
        return "diplomacy"
    else:
        return "conflict"  # Battles, Violence against civilians, Explosions -> conflict

print(f"Total rows found: {len(df)}. Converting and inserting into MongoDB...")

documents = []
for _, row in df.iterrows():
    # Severity ko 1 se 10 ke beech limit karna (Schema rule: min 1, max 10)
    raw_fat = int(row["fatalities"]) if pd.notna(row["fatalities"]) else 0
    sev = min(max(raw_fat, 1), 10)  # 0 ho toh 1 banega, 10 se bada ho toh 10 banega

    doc = {
        "date": datetime.strptime(str(row["week"]), "%Y-%m-%d"),
        "location": {
            "country": str(row["country"]),
            "region": str(row["admin1"]) if pd.notna(row["admin1"]) else str(row["region"]),
        },
        "type": map_event_type(row["event_type"]),
        "severity": sev,
        "actors_involved": [str(row["country"])],
        "source_id": "acled",
        "summary": f"{row['event_type']} - {row['sub_event_type']} in {row['country']}"[:490],
        "status": "verified",
    }
    documents.append(doc)

# Purana data clear karke real data insert karna
db.events.delete_many({})
db.events.insert_many(documents)

# Sources collection mein 'acled' bhi add kar dete hain taaki $lookup (Source Reliability) me dikhe
db.sources.update_one(
    {"_id": "acled"},
    {"$set": {"name": "ACLED Global Data", "credibility_score": 95, "country": "Global"}},
    upsert=True,
)

print(f"Successfully imported {db.events.count_documents({})} real events into MongoDB!")