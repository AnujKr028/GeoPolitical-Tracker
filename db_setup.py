
"""
db_setup.py
Connection + collections + $jsonSchema validation + indexes.
Run once: python db_setup.py
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

# Local development: reads from .env
# Render deployment: reads environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "geopolitics_tracker"

EVENT_TYPES = ["conflict", "sanction", "diplomacy", "protest", "election"]
ACTOR_TYPES = ["state", "organization", "non-state-group"]
RELATION_TYPES = ["ally", "rival", "sanction", "trade-partner"]
EVENT_STATUS = ["reported", "verified", "retracted"]


def get_db():
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")
    return client[DB_NAME]


# ----------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------

ACTORS_SCHEMA = {
    "bsonType": "object",
    "required": ["_id", "name", "type", "region"],
    "properties": {
        "_id": {"bsonType": "string", "description": "short code e.g. IND"},
        "name": {"bsonType": "string", "minLength": 2},
        "type": {"enum": ACTOR_TYPES},
        "region": {"bsonType": "string"},
        "aligned_with": {
            "bsonType": "array",
            "items": {"bsonType": "string"}
        },
    },
}

SOURCES_SCHEMA = {
    "bsonType": "object",
    "required": ["_id", "name", "credibility_score", "country"],
    "properties": {
        "_id": {"bsonType": "string"},
        "name": {"bsonType": "string"},
        "credibility_score": {
            "bsonType": ["int", "double"],
            "minimum": 0,
            "maximum": 100
        },
        "country": {"bsonType": "string"},
    },
}

RELATIONS_SCHEMA = {
    "bsonType": "object",
    "required": ["actor_a", "actor_b", "relation_type", "since"],
    "properties": {
        "actor_a": {"bsonType": "string"},
        "actor_b": {"bsonType": "string"},
        "relation_type": {"enum": RELATION_TYPES},
        "since": {
            "bsonType": "int",
            "minimum": 1900,
            "maximum": 2100
        },
    },
}

EVENTS_SCHEMA = {
    "bsonType": "object",
    "required": [
        "date",
        "location",
        "type",
        "severity",
        "actors_involved",
        "source_id",
        "status"
    ],
    "properties": {
        "date": {"bsonType": "date"},
        "location": {
            "bsonType": "object",
            "required": ["country", "region"],
            "properties": {
                "country": {"bsonType": "string"},
                "region": {"bsonType": "string"},
            },
        },
        "type": {"enum": EVENT_TYPES},
        "severity": {
            "bsonType": "int",
            "minimum": 1,
            "maximum": 10
        },
        "actors_involved": {
            "bsonType": "array",
            "minItems": 1,
            "items": {"bsonType": "string"},
        },
        "source_id": {"bsonType": "string"},
        "summary": {
            "bsonType": "string",
            "maxLength": 500
        },
        "status": {"enum": EVENT_STATUS},
    },
}

SCHEMAS = {
    "actors": ACTORS_SCHEMA,
    "sources": SOURCES_SCHEMA,
    "relations": RELATIONS_SCHEMA,
    "events": EVENTS_SCHEMA,
}


def _create_or_update(db, name, schema):
    opts = {
        "validator": {"$jsonSchema": schema},
        "validationLevel": "strict",
        "validationAction": "error",
    }

    if name in db.list_collection_names():
        db.command("collMod", name, **opts)
    else:
        db.create_collection(name, **opts)


def setup_database(db):
    for name, schema in SCHEMAS.items():
        _create_or_update(db, name, schema)

    # Indexes
    db.events.create_index([
        ("location.country", ASCENDING),
        ("date", DESCENDING)
    ])

    db.events.create_index("severity")
    db.events.create_index("type")
    db.events.create_index("actors_involved")

    db.actors.create_index("name", unique=True)

    db.relations.create_index(
        [
            ("actor_a", ASCENDING),
            ("actor_b", ASCENDING),
            ("relation_type", ASCENDING)
        ],
        unique=True
    )

    print("Collections, validators and indexes ready.")


if __name__ == "__main__":
    setup_database(get_db())
