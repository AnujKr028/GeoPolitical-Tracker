"""
crud.py
Step 3: CRUD operations using PyMongo.
Run demo:  python crud.py
"""
from datetime import datetime
from bson import ObjectId
from pymongo.errors import WriteError
from db_setup import get_db


# ------------------------------------------------------------ helpers
def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def show(docs):
    for e in docs:
        print(f"  {e['date']:%Y-%m-%d} | {e['location']['country']:<14} | "
              f"{e['type']:<9} | sev {e['severity']:>2} | {e['status']:<9} | {e['summary'][:45]}")


# ------------------------------------------------------------ CREATE
def create_event(db, date_str, country, region, etype, severity,
                 actors, source_id, summary="", status="reported"):
    """Insert one event. Python-side checks + MongoDB $jsonSchema checks."""
    date = parse_date(date_str)

    # $jsonSchema me "future date nahi" check nahi ho sakta, isliye Python me:
    if date > datetime.now():
        raise ValueError("Event date cannot be in the future.")

    # referential integrity: Mongo khud foreign key check nahi karta
    known = {a["_id"] for a in db.actors.find({"_id": {"$in": actors}}, {"_id": 1})}
    missing = set(actors) - known
    if missing:
        raise ValueError(f"Unknown actors: {missing}")
    if db.sources.count_documents({"_id": source_id}) == 0:
        raise ValueError(f"Unknown source: {source_id}")

    doc = {
        "date": date,
        "location": {"country": country, "region": region},
        "type": etype,
        "severity": severity,
        "actors_involved": actors,
        "source_id": source_id,
        "summary": summary,
        "status": status,
    }
    try:
        return db.events.insert_one(doc).inserted_id
    except WriteError as e:
        raise ValueError(f"Schema validation failed: {e.details['errmsg']}")


def add_actor(db, actor_id, name, atype, region, aligned_with=None):
    return db.actors.insert_one({
        "_id": actor_id, "name": name, "type": atype,
        "region": region, "aligned_with": aligned_with or [],
    }).inserted_id


def add_events_bulk(db, events):
    """events = list of full documents; insert_many (ordered=False: ek fail ho to baaki chalein)."""
    return db.events.insert_many(events, ordered=False).inserted_ids


# ------------------------------------------------------------ READ
def get_events(db, country=None, etype=None, min_sev=None, max_sev=None,
               start=None, end=None, status=None, limit=20):
    q = {}
    if country:
        q["location.country"] = country
    if etype:
        q["type"] = etype
    if status:
        q["status"] = status
    if min_sev is not None or max_sev is not None:
        q["severity"] = {}
        if min_sev is not None:
            q["severity"]["$gte"] = min_sev
        if max_sev is not None:
            q["severity"]["$lte"] = max_sev
    if start or end:
        q["date"] = {}
        if start:
            q["date"]["$gte"] = parse_date(start)
        if end:
            q["date"]["$lte"] = parse_date(end)
    return list(db.events.find(q).sort("date", -1).limit(limit))


def get_events_by_actor(db, actor_id):
    # actors_involved array hai, to seedha equality match array element pe chalta hai
    return list(db.events.find({"actors_involved": actor_id}).sort("date", 1))


def get_event(db, event_id):
    return db.events.find_one({"_id": ObjectId(event_id)})


# ------------------------------------------------------------ UPDATE
def update_severity(db, event_id, new_sev):
    r = db.events.update_one({"_id": ObjectId(event_id)}, {"$set": {"severity": new_sev}})
    return r.modified_count


def set_status(db, event_id, status):
    r = db.events.update_one({"_id": ObjectId(event_id)}, {"$set": {"status": status}})
    return r.modified_count


def add_actor_to_event(db, event_id, actor_id):
    # $addToSet: duplicate nahi banega ($push se ban jata)
    r = db.events.update_one({"_id": ObjectId(event_id)},
                             {"$addToSet": {"actors_involved": actor_id}})
    return r.modified_count


def add_alignment(db, actor_id, other_id):
    r = db.actors.update_one({"_id": actor_id}, {"$addToSet": {"aligned_with": other_id}})
    return r.modified_count


def set_status_by_source(db, source_id, from_status, to_status):
    """update_many: ek source ke saare events ka status ek saath badlo."""
    r = db.events.update_many({"source_id": source_id, "status": from_status},
                              {"$set": {"status": to_status}})
    return r.modified_count


def update_source_credibility(db, source_id, score):
    r = db.sources.update_one({"_id": source_id}, {"$set": {"credibility_score": score}})
    return r.modified_count


# ------------------------------------------------------------ DELETE
def delete_event(db, event_id):
    return db.events.delete_one({"_id": ObjectId(event_id)}).deleted_count


def delete_retracted(db):
    """Retracted news ek saath hatao."""
    return db.events.delete_many({"status": "retracted"}).deleted_count


# ------------------------------------------------------------ DEMO
if __name__ == "__main__":
    db = get_db()

    print("\n--- CREATE")
    eid = create_event(db, "2025-11-03", "India", "South Asia", "diplomacy", 3,
                       ["IND", "CHN"], "thehindu", "DEMO: bilateral talks", status="reported")
    print("Inserted _id:", eid)

    print("\n--- CREATE (should fail: future date)")
    try:
        create_event(db, "2030-01-01", "India", "South Asia", "diplomacy", 3, ["IND"], "reuters")
    except ValueError as e:
        print("Rejected:", e)

    print("\n--- CREATE (should fail: schema, severity 15)")
    try:
        create_event(db, "2025-11-04", "India", "South Asia", "diplomacy", 15, ["IND"], "reuters")
    except ValueError as e:
        print("Rejected:", str(e)[:120])

    print("\n--- READ: conflicts with severity >= 8")
    show(get_events(db, etype="conflict", min_sev=8))

    print("\n--- READ: Jun 2025 events")
    show(get_events(db, start="2025-06-01", end="2025-06-30"))

    print("\n--- READ: events involving IRN")
    show(get_events_by_actor(db, "IRN"))

    print("\n--- UPDATE one: severity 3 -> 5")
    print("modified:", update_severity(db, eid, 5))

    print("\n--- UPDATE one: add actor USA ($addToSet)")
    print("modified:", add_actor_to_event(db, eid, "USA"))
    print("actors now:", get_event(db, eid)["actors_involved"])

    print("\n--- UPDATE many: aljazeera verified -> reported, then back")
    print("modified:", set_status_by_source(db, "aljazeera", "verified", "reported"))
    print("restored:", set_status_by_source(db, "aljazeera", "reported", "verified"))

    print("\n--- UPDATE source credibility")
    print("modified:", update_source_credibility(db, "dawn", 80))
    update_source_credibility(db, "dawn", 78)  # original value wapas

    print("\n--- DELETE one (retract demo event)")
    set_status(db, eid, "retracted")
    print("deleted:", delete_event(db, eid))

    print("\n--- DELETE many (retracted)")
    print("deleted:", delete_retracted(db))
