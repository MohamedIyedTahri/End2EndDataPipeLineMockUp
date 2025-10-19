import argparse
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers
import datetime
import random

def generate_random_date():
    """Generate a random datetime within the past year"""
    today = datetime.datetime.now()
    days_offset = random.randint(0, 365)
    return (today - datetime.timedelta(days=days_offset)).isoformat()

def transform_document(doc, es_index):
    return {
        "_index": es_index,
        "_id": str(doc.get("_id")),
        "_source": {
            "titre": "Titre générique",  # Placeholder
            "contenu": doc.get("Text", ""),
            "auteur": "anonyme",         # Placeholder
            "date": generate_random_date(),
            "URL": "https://example.com/post",  # Placeholder
            "langue": doc.get("Language", "unknown"),
            "sentiment": doc.get("Sentiment_Ensemble_Label", "neutral"),
            "score": float(doc.get("Sentiment_Ensemble_Score") or 0.0)
        }
    }

def create_index_if_not_exists(es, index_name):
    if not es.indices.exists(index=index_name):
        es.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "titre": {"type": "text"},
                        "contenu": {"type": "text"},
                        "auteur": {"type": "keyword"},
                        "date": {"type": "date"},
                        "URL": {"type": "keyword"},
                        "langue": {"type": "keyword"},
                        "sentiment": {"type": "keyword"},
                        "score": {"type": "float"}
                    }
                }
            }
        )
        print(f"✅ Index '{index_name}' created.")
    else:
        print(f"ℹ️ Index '{index_name}' already exists.")

def main(args):
    # MongoDB setup
    mongo_client = MongoClient(args.mongo_uri)
    mongo_db = mongo_client[args.db]
    mongo_collection = mongo_db[args.collection]

    # Elasticsearch setup with optional basic auth & SSL verification control
    es_kwargs = {
        "hosts": [args.es_uri],
        "verify_certs": not args.no_verify_ssl
    }
    if args.es_user and args.es_password:
        es_kwargs["basic_auth"] = (args.es_user, args.es_password)

    es = Elasticsearch(**es_kwargs)

    # Create index if needed
    create_index_if_not_exists(es, args.es_index)

    # Prepare documents
    mongo_docs = mongo_collection.find()
    actions = (transform_document(doc, args.es_index) for doc in mongo_docs)

    # Bulk insert
    try:
        helpers.bulk(es, actions)
        print("✅ All documents indexed into Elasticsearch.")
    except Exception as e:
        print(f"❌ Error indexing documents: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index MongoDB documents into Elasticsearch")

    parser.add_argument("--mongo-uri", type=str, default="mongodb://localhost:27017/", help="MongoDB URI (e.g., mongodb://localhost:27017/)")
    parser.add_argument("--db", type=str, default="harcelement", help="MongoDB database name")
    parser.add_argument("--collection", type=str, default="enriched", help="MongoDB collection name")
    parser.add_argument("--es-uri", type=str, default="http://localhost:9200", help="Elasticsearch URI (e.g., http://localhost:9200)")
    parser.add_argument("--es-index", type=str, default="harcelement_posts", help="Elasticsearch index name")
    parser.add_argument("--es-user", type=str, default="elastic", help="Elasticsearch username (optional)")
    parser.add_argument("--es-password", type=str, default="Q*aPCff9cD3Q6WDKjYpR", help="Elasticsearch password (optional)")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification")

    args = parser.parse_args()
    main(args)
