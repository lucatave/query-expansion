import argparse
from data import (wait_for_db, create_db,
                  get_data, close_connection,
                  from_db_to_socialpagerank_matPU,
                  from_db_to_socialpagerank_matAP,
                  from_db_to_socialpagerank_matUA,
                  from_socialpagerank_to_db,
                  randomize_matP)
from socialpagerank import (socialpagerank,
                            query_expansion)
from logging import (basicConfig, debug, info,
                     DEBUG, INFO, ERROR, CRITICAL)
from sys import stderr

if __name__ == '__main__':
    basicConfig(stream=stderr, level=INFO)
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
    parser.add_argument("-spr", "--socialpagerank",
                        help="evaluates rank of documents, users and \
                        annotations with spr",
                        action="store_true")

    args = parser.parse_args()
    debug("CONNECTING TO DATABASE")
    db = wait_for_db()
    debug("CONNECTED TO DATABASE")
    if args.create:
        create_db(db)
    if args.update:
        info("RETRIEVING TWITTER DATA")
        get_data()
        info("FINISHED RETRIEVING TWITTER DATA")
    if args.socialpagerank:
        matPU = from_db_to_socialpagerank_matPU()
        matAP = from_db_to_socialpagerank_matAP()
        matUA = from_db_to_socialpagerank_matUA()
        matP = randomize_matP(matPU, matAP, matUA)
        from_socialpagerank_to_db(socialpagerank(matPU, matAP, matUA, matP))
    if args.query:
        query = args.query
        exp_query = query_expansion(query)
        info("ORIGINAL QUERY:\n", query)
        info("EXPANDED QUERY:\n",)
    close_connection()
