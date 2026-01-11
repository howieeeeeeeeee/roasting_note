#!/usr/bin/env python3
"""
Cleanup script for test data.

This script removes all documents marked with `test_data: True` from the local database.
Run this if tests fail unexpectedly and leave orphaned test data.

Usage:
    python tests/cleanup_test_data.py

Or from Python:
    from tests.cleanup_test_data import cleanup_all_test_data
    cleanup_all_test_data()
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient


def get_local_db():
    """Get connection to local MongoDB."""
    mongo_uri = os.environ.get('MONGO_URI_LOCAL', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    return client.roastlogger


def cleanup_all_test_data():
    """
    Remove all test data from local database.

    Test data is identified by the `test_data: True` field.

    Returns:
        dict: Count of deleted documents by collection
    """
    db = get_local_db()

    results = {
        'beans_deleted': 0,
        'roasts_deleted': 0,
        'temp_logs_deleted': 0
    }

    # Clean beans
    result = db.beans.delete_many({'test_data': True})
    results['beans_deleted'] = result.deleted_count

    # Clean roasts
    result = db.roasts.delete_many({'test_data': True})
    results['roasts_deleted'] = result.deleted_count

    # Clean temp log files for test roasts
    temp_logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_logs')
    if os.path.exists(temp_logs_dir):
        for filename in os.listdir(temp_logs_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(temp_logs_dir, filename)
                # Check if this is test data by trying to find roast
                roast_id = filename.replace('.csv', '')
                try:
                    # If roast doesn't exist or is test data, delete the file
                    from bson.objectid import ObjectId
                    roast = db.roasts.find_one({'_id': ObjectId(roast_id)})
                    if roast is None or roast.get('test_data'):
                        os.remove(filepath)
                        results['temp_logs_deleted'] += 1
                except:
                    pass  # Invalid filename format, skip

    return results


def show_test_data_count():
    """Show count of test data documents in database."""
    db = get_local_db()

    beans_count = db.beans.count_documents({'test_data': True})
    roasts_count = db.roasts.count_documents({'test_data': True})

    print(f"Test data in database:")
    print(f"  Beans:  {beans_count}")
    print(f"  Roasts: {roasts_count}")

    return {'beans': beans_count, 'roasts': roasts_count}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Cleanup test data from database')
    parser.add_argument('--count', '-c', action='store_true',
                        help='Only show count of test data, do not delete')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Skip confirmation prompt')

    args = parser.parse_args()

    if args.count:
        show_test_data_count()
    else:
        counts = show_test_data_count()
        total = counts['beans'] + counts['roasts']

        if total == 0:
            print("\nNo test data to clean up.")
            sys.exit(0)

        if not args.force:
            response = input(f"\nDelete {total} test documents? [y/N] ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(0)

        results = cleanup_all_test_data()
        print(f"\nCleanup complete:")
        print(f"  Beans deleted:  {results['beans_deleted']}")
        print(f"  Roasts deleted: {results['roasts_deleted']}")
        print(f"  Temp logs deleted: {results['temp_logs_deleted']}")
