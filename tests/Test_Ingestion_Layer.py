import argparse
import os
import sys
import uuid
from pathlib import Path

import pandas as pd
import pytest
from elasticsearch import Elasticsearch
from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingestion_Layer import ingest_to_mongo, indexation


@pytest.fixture(scope="module")
def mongo_uri() -> str:
    return os.getenv("MONGO_URI", "mongodb://localhost:27017/")


@pytest.fixture(scope="module")
def es_config() -> dict[str, str]:
    return {
        "uri": os.getenv("ES_URI", "http://localhost:9200"),
        "user": os.getenv("ES_USER", "elastic"),
        "password": os.getenv("ES_PASSWORD", "Q*aPCff9cD3Q6WDKjYpR"),
    }


@pytest.fixture(scope="module")
def mongo_client(mongo_uri: str) -> MongoClient:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except Exception as exc:  # pragma: no cover - integration gating
        pytest.skip(f"MongoDB not reachable at {mongo_uri}: {exc}")
    yield client
    client.close()


@pytest.fixture(scope="module")
def es_client(es_config: dict[str, str]) -> Elasticsearch:
    es_kwargs: dict[str, object] = {
        "hosts": [es_config["uri"]],
    }
    if es_config.get("user") and es_config.get("password"):
        es_kwargs["basic_auth"] = (es_config["user"], es_config["password"])

    es = Elasticsearch(**es_kwargs)
    try:
        if not es.ping():  # pragma: no cover - integration gating
            pytest.skip(f"Elasticsearch ping failed at {es_config['uri']}")
    except Exception as exc:  # pragma: no cover - integration gating
        pytest.skip(f"Elasticsearch not reachable at {es_config['uri']}: {exc}")
    yield es
    es.close()


def _run_ingest(csv_path: Path, mongo_uri: str, db_name: str, collection: str) -> None:
    original_argv = sys.argv
    try:
        sys.argv = [
            "ingest_to_mongo",
            "--csv-path",
            str(csv_path),
            "--mongo-uri",
            mongo_uri,
            "--db-name",
            db_name,
            "--collection-name",
            collection,
        ]
        ingest_to_mongo.main()
    finally:
        sys.argv = original_argv


def _run_indexation(
    mongo_uri: str,
    db_name: str,
    collection: str,
    es_uri: str,
    es_index: str,
    es_user: str,
    es_password: str,
    no_verify_ssl: bool = True,
) -> None:
    args = argparse.Namespace(
        mongo_uri=mongo_uri,
        db=db_name,
        collection=collection,
        es_uri=es_uri,
        es_index=es_index,
        es_user=es_user,
        es_password=es_password,
        no_verify_ssl=no_verify_ssl,
    )
    indexation.main(args)


def test_ingest_to_mongo_integration(tmp_path: Path, mongo_client: MongoClient, mongo_uri: str) -> None:
    db_name = f"harcelement_test_{uuid.uuid4().hex[:8]}"
    collection_name = "posts"
    df = pd.DataFrame({"Text": ["Hello", "Bonjour"], "Language": ["en", "fr"]})
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)

    try:
        _run_ingest(csv_path, mongo_uri, db_name, collection_name)
        inserted = list(mongo_client[db_name][collection_name].find())
        assert len(inserted) == len(df)
        assert all("Id_Post" in doc for doc in inserted)
    finally:
        mongo_client.drop_database(db_name)


def test_indexation_integration(
    tmp_path: Path,
    mongo_client: MongoClient,
    es_client: Elasticsearch,
    mongo_uri: str,
    es_config: dict[str, str],
) -> None:
    db_name = f"harcelement_test_{uuid.uuid4().hex[:8]}"
    collection_name = "posts"
    es_index = f"harcelement_posts_{uuid.uuid4().hex[:8]}"

    df = pd.DataFrame(
        {
            "Text": ["Great day", "Terrible service"],
            "Language": ["en", "en"],
            "Sentiment_Ensemble_Label": ["positive", "negative"],
            "Sentiment_Ensemble_Score": [0.76, -0.65],
        }
    )
    csv_path = tmp_path / "sentiment.csv"
    df.to_csv(csv_path, index=False)

    try:
        _run_ingest(csv_path, mongo_uri, db_name, collection_name)
        _run_indexation(
            mongo_uri,
            db_name,
            collection_name,
            es_config["uri"],
            es_index,
            es_config.get("user", ""),
            es_config.get("password", ""),
        )

        es_client.indices.refresh(index=es_index)
        count = es_client.count(index=es_index)["count"]
        assert count == len(df)
    finally:
        mongo_client.drop_database(db_name)
        if es_client.indices.exists(index=es_index):
            es_client.indices.delete(index=es_index)
