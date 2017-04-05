import argparse
from data import (wait_for_db, create_db,
                  get_aa_subset, get_data)
from socialpagerank import query_expansion

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query",
                        help="query to be expanded",
                        type=str)
    parser.add_argument("-c", "--create",
                        help="creates a new db instanciated with new data",
                        action="store_true")
    parser.add_argument("-u", "--update",
                        help="adds new data to the instanciated db",
                        action="store_true")

    args = parser.parse_args()
    print("CONNECTING TO DATABASE")
    wait_for_db()
    print("CONNECTED TO DATABASE")
    if args.query:
        query = args.query
        query_expansion(query, get_aa_subset())
    if args.create:
        create_db()
    if args.update:
        try:
            print("RETRIEVING TWITTER DATA")
            get_data()
            print("FINISHED RETRIEVING TWITTER DATA")
        except:
            print("ERROR: An error occured while trying to get new data.")
