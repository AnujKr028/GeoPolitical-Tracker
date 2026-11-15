"""
ml_model.py
K-Means clustering to find high-risk conflict hotspots from MongoDB data.
"""
import pandas as pd
from sklearn.cluster import KMeans
from db_setup import get_db

def get_ml_conflict_clusters(db):
    # MongoDB se data fetch karna
    events = list(db.events.find({}, {"location.country": 1, "severity": 1}))
    if not events:
        return None
    
    df = pd.DataFrame(events)
    df["country"] = df["location"].apply(lambda x: x.get("country"))
    
    # Country-wise severity sum / average calculate karna
    country_stats = df.groupby("country").agg(
        total_severity=("severity", "sum"),
        event_count=("severity", "count")
    ).reset_index()
    
    if len(country_stats) < 3:
        return country_stats # Agar data kam ho toh direct return karein
    
    # K-Means Clustering Model (3 clusters: Low, Medium, High Risk)
    X = country_stats[["total_severity", "event_count"]]
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    country_stats["risk_cluster"] = kmeans.fit_predict(X)
    
    # Cluster labels mapping
    cluster_names = {0: "Low Risk", 1: "Medium Risk", 2: "High Risk Hotspot"}
    country_stats["risk_level"] = country_stats["risk_cluster"].map(cluster_names)
    
    return country_stats.sort_values(by="total_severity", ascending=False)