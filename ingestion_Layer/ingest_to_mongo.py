import pandas as pd
from pymongo import MongoClient
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Load CSV into MongoDB and add Id_Post field")
    
    parser.add_argument("--csv-path", type=str, help="Path to input CSV file")
    parser.add_argument("--mongo-uri", type=str, help="MongoDB URI (default: mongodb://localhost:27017/)", default="mongodb://localhost:27017/")
    parser.add_argument("--db-name", type=str, help="MongoDB database name (default: harcelement)", default="harcelement")
    parser.add_argument("--collection-name", type=str, help="MongoDB collection name (default: posts)", default="posts")
    
    args = parser.parse_args()
    
    # Prompt if missing args
    if not args.csv_path:
        args.csv_path = input("Enter path to CSV file (e.g. ../data/clean/posts.csv): ").strip()
    if not args.mongo_uri:
        args.mongo_uri = input("Enter MongoDB URI (default: mongodb://localhost:27017/): ").strip() or "mongodb://localhost:27017/"
    if not args.db_name:
        args.db_name = input("Enter MongoDB database name (default: harcelement): ").strip() or "harcelement"
    if not args.collection_name:
        args.collection_name = input("Enter MongoDB collection name (default: posts): ").strip() or "posts"
    
    # Load CSV
    try:
        df = pd.read_csv(args.csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Connect to MongoDB
    try:
        client = MongoClient(args.mongo_uri)
        db = client[args.db_name]
        collection = db[args.collection_name]
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert DataFrame to dict
    data = df.to_dict(orient='records')
    
    # Insert documents
    try:
        result = collection.insert_many(data)
        print(f"Inserted {len(result.inserted_ids)} documents.")
    except Exception as e:
        print(f"Error inserting documents: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Update documents to add Id_Post field (copy of _id)
    try:
        collection.update_many(
            {'_id': {'$in': result.inserted_ids}},
            [{'$set': {'Id_Post': '$_id'}}]
        )
        print("Added 'Id_Post' field to all inserted documents.")
    except Exception as e:
        print(f"Error updating documents: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
