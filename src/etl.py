"""
Load raw CSVs into DuckDB and build the analytical tables.
"""
import duckdb

DB_PATH = "data/analytics.duckdb"


def build_database(db_path=DB_PATH):
    con = duckdb.connect(db_path)

    # Raw tables straight from the CSVs
    for name in ["users", "events", "transactions"]:
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto('data/{name}.csv')")

    # Derived tables from the SQL files
    with open("sql/user_funnel.sql") as f:
        con.execute(f.read())

    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["users", "events", "transactions", "user_funnel"]}
    con.close()
    return counts


if __name__ == "__main__":
    for table, n in build_database().items():
        print(f"{table:15s} {n:>10,}")