"""
pipelines.py
Step 4: Advanced Aggregation Pipelines ($group, $dateToString, $lookup, $graphLookup, $bucket, $facet).
Run demo: python pipelines.py
"""
from db_setup import get_db

db = get_db()

# 1. Country-wise count + avg severity ($group)
def country_severity_stats(db):
    pipeline = [
        {
            "$group": {
                "_id": "$location.country",
                "total_events": {"$sum": 1},
                "avg_severity": {"$avg": "$severity"},
                "max_severity": {"$max": "$severity"}
            }
        },
        {"$sort": {"total_events": -1}}
    ]
    return list(db.events.aggregate(pipeline))

# 2. Monthly escalation trend ($dateToString)
def monthly_escalation_trend(db):
    pipeline = [
        {
            "$project": {
                "month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}},
                "severity": 1,
                "type": 1
            }
        },
        {
            "$group": {
                "_id": "$month",
                "event_count": {"$sum": 1},
                "avg_severity": {"$avg": "$severity"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    return list(db.events.aggregate(pipeline))

# 3. Source reliability ranking ($lookup)
def source_reliability_ranking(db):
    pipeline = [
        {
            "$group": {
                "_id": "$source_id",
                "reports_count": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "sources",
                "localField": "_id",
                "foreignField": "_id",
                "as": "source_info"
            }
        },
        {"$unwind": "$source_info"},
        {
            "$project": {
                "source_name": "$source_info.name",
                "credibility": "$source_info.credibility_score",
                "reports_count": 1
            }
        },
        {"$sort": {"credibility": -1}}
    ]
    return list(db.events.aggregate(pipeline))

# 4. Alliance chain ($graphLookup)
def get_actor_alliance_chain(db, start_actor):
    pipeline = [
        {"$match": {"_id": start_actor}},
        {
            "$graphLookup": {
                "from": "actors",
                "startWith": "$aligned_with",
                "connectFromField": "aligned_with",
                "connectToField": "_id",
                "as": "alliance_network",
                "maxDepth": 2,
                "depthField": "chain_level"
            }
        }
    ]
    return list(db.actors.aggregate(pipeline))

# 5. Severity bands ($bucket)
def severity_bands(db):
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$severity",
                "boundaries": [1, 4, 7, 11],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1},
                    "events": {"$push": "$summary"}
                }
            }
        }
    ]
    return list(db.events.aggregate(pipeline))

# 6. Dashboard in one query ($facet)
def dashboard_facet(db):
    pipeline = [
        {
            "$facet": {
                "top_countries": [
                    {"$group": {"_id": "$location.country", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 3}
                ],
                "event_types": [
                    {"$group": {"_id": "$type", "count": {"$sum": 1}}}
                ],
                "severity_stats": [
                    {"$group": {"_id": None, "avg_sev": {"$avg": "$severity"}}}
                ]
            }
        }
    ]
    return list(db.events.aggregate(pipeline))


if __name__ == "__main__":
    print("\n--- 1. Country-wise stats ---")
    for r in country_severity_stats(db)[:3]:
        print(r)

    print("\n--- 2. Monthly escalation trend ---")
    for r in monthly_escalation_trend(db)[:3]:
        print(r)

    print("\n--- 3. Source reliability ranking ---")
    for r in source_reliability_ranking(db):
        print(r)

    print("\n--- 4. Alliance Chain for USA ---")
    for r in get_actor_alliance_chain(db, "USA"):
        print(f"Actor: {r['_id']}, Network count: {len(r['alliance_network'])}")

    print("\n--- 5. Severity Bands ---")
    for r in severity_bands(db):
        print(r)

    print("\n--- 6. Dashboard Facet ---")
    print(dashboard_facet(db))