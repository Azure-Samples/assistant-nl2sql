import psycopg2
from psycopg2 import sql
from .function import Function, Property
from .config import PGConfig as config


class GetDBSchema(Function):
    def __init__(self):
        super().__init__(
            name="get_db_schema",
            description="Get the schema of the postgres database",
        )

    def function(self):
        conn = psycopg2.connect(**config().db_params)
        cursor = conn.cursor()

        # Query to get the table creation statements
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        )

        tables = cursor.fetchall()
        create_statements = []

        for table in tables:
            table_name = table[0]
            if table_name.startswith("pg"):
                continue

            cursor.execute(
                sql.SQL(
                    """
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
            """
                ),
                [table_name],
            )
            columns = cursor.fetchall()

            create_statement = f"CREATE TABLE {table_name} ("
            column_definitions = []
            for column in columns:
                column_name, data_type, char_max_length, is_nullable = column
                column_def = f"{column_name} {data_type}"
                if char_max_length:
                    column_def += f"({char_max_length})"
                if is_nullable == "NO":
                    column_def += " NOT NULL"
                column_definitions.append(column_def)

            create_statement += ", ".join(column_definitions) + ");"
            create_statements.append(create_statement)

            # Get sample rows
            limit = 3
            cursor.execute(sql.SQL(f"SELECT * FROM {table_name} LIMIT {limit}"))
            rows = cursor.fetchall()
            columns_str = "\t".join([desc[0] for desc in cursor.description])
            rows_str = "\n".join(["\t".join(map(str, row)) for row in rows])
            sample_rows_info = (
                f"{limit} rows from {table_name} table:\n"
                f"{columns_str}\n"
                f"{rows_str}"
            )

        conn.close()

        table_info = "\n\n".join(create_statements) + "\n\n" + sample_rows_info

        return table_info


class RunSQLQuery(Function):
    def __init__(self):
        super().__init__(
            name="run_sql_query",
            description="Run a SQL query on the postgres database",
            parameters=[
                Property(
                    name="table_name",
                    description="The table name to run the query on",
                    type="string",
                    required=True,
                ),
                Property(
                    name="query",
                    description="The SQL query to run",
                    type="string",
                    required=True,
                ),
            ],
        )

    def function(self, table_name, query):
        try:
            conn = psycopg2.connect(**config().db_params)
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            return "\n".join([str(result) for result in results])
        except psycopg2.Error as e:
            # Undefined table error code
            if e.pgcode == "42P01":
                return f"Error running query: {e}\n Table {table_name} does not exist"
            elif e.pgcode == "42703":
                conn = psycopg2.connect(**config().db_params)
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                colnames = [desc[0] for desc in cursor.description]
                return (
                    f"On of the columns does not exist"
                    + "\n The following columns exist:\n"
                    + " | ".join(colnames)
                )
            else:
                # List the available tables
                conn = psycopg2.connect(**config().db_params)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                )
                tables = cursor.fetchall()
                table_names = [table[0] for table in tables]
                return f"Error running query: {e}\nAvailable tables: {table_names}"


class ListTables(Function):
    def __init__(self):
        super().__init__(
            name="list_tables",
            description="List the tables in the postgres database",
        )

    def function(self):
        try:
            conn = psycopg2.connect(**config().db_params)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )
            tables = cursor.fetchall()
            table_names = [
                table[0] for table in tables if not table[0].startswith("pg")
            ]
            conn.close()
            return "\n".join(table_names)
        except psycopg2.Error as e:
            return f"Error listing tables: {e}"


class FetchDistinctValues(Function):
    def __init__(self):
        super().__init__(
            name="fetch_distinct_values",
            description="Fetch the first 10 distinct values of a specified column for a certain table",
            parameters=[
                Property(
                    name="table_name",
                    description="The table name to fetch distinct values",
                    type="string",
                    required=True,
                ),
                Property(
                    name="column_name",
                    description="The column name to fetch distinct values",
                    type="string",
                    required=True,
                ),
            ],
        )

    def function(self, table_name, column_name):
        try:
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(**config().db_params)
            cursor = conn.cursor()

            # Execute the query to fetch distinct values with a limit
            query = sql.SQL(
                "SELECT {}, COUNT(*) as qty \
                             FROM {} \
                             GROUP BY {} \
                             ORDER BY qty DESC \
                             LIMIT 10;"
            ).format(
                sql.Identifier(column_name),
                sql.Identifier(table_name),
                sql.Identifier(column_name),
            )
            cursor.execute(query)
            rows = cursor.fetchall()

            # Fetch column names
            colnames = [desc[0] for desc in cursor.description]

            # Close the cursor and connection
            cursor.close()
            conn.close()

            # Create a single string with columns and rows
            result = " | ".join(colnames) + "\n"
            result += "\n".join([" | ".join(map(str, row)) for row in rows])

            return result

        except psycopg2.Error as e:
            if e.pgcode == "42703":  # Undefined column error code
                # return the available column names
                conn = psycopg2.connect(**config.db_params)
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {sql.Identifier(table_name)} LIMIT 1;")
                colnames = [desc[0] for desc in cursor.description]
                return (
                    f"The column {column_name} does not exist"
                    + "\n The following columns exist:\n"
                    + " | ".join(colnames)
                )
            else:
                print(f"Error fetching distinct values: {e}")
                return f"Error fetching distinct values: {e}"


class FetchSimilarValues(Function):
    def __init__(self):
        super().__init__(
            name="fetch_similar_values",
            description="Fetch the most similar values of a specified column to a given value",
            parameters=[
                Property(
                    name="table_name",
                    description="The table name to fetch similar values",
                    type="string",
                    required=True,
                ),
                Property(
                    name="column_name",
                    description="The column name to fetch similar values",
                    type="string",
                    required=True,
                ),
                Property(
                    name="value",
                    description="The value to find similar values",
                    type="string",
                    required=True,
                ),
            ],
        )

    def function(self, table_name, column_name, value):
        try:
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(**config().db_params)
            cursor = conn.cursor()

            # Execute the query to fetch distinct values with a limit
            query = sql.SQL(
                f"CREATE EXTENSION IF NOT EXISTS pg_trgm; \
                              SELECT {column_name}, \
                                     similarity(CAST({column_name} AS TEXT), \
                                     '{value}') AS similarity_score \
                              FROM {table_name} \
                              WHERE similarity(CAST({column_name} AS TEXT), '{value}') > 0.7  \
                              ORDER BY similarity_score DESC \
                              LIMIT 10;"
            )

            cursor.execute(query)
            rows = cursor.fetchall()

            if len(rows) == 0:
                return f"No similar values found for {value} in {column_name} for table {table_name}"

            # Fetch column names
            colnames = [desc[0] for desc in cursor.description]

            # Close the cursor and connection
            cursor.close()
            conn.close()

            # Create a single string with columns and rows
            result = " | ".join(colnames) + "\n"
            result += "\n".join([" | ".join(map(str, row)) for row in rows])

            return result

        except psycopg2.Error as e:
            if e.pgcode == "42703":  # Undefined column error code
                # return the available column names
                conn = psycopg2.connect(**config().db_params)
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                colnames = [desc[0] for desc in cursor.description]
                return (
                    f"The column {column_name} does not exist"
                    + "\n The following columns exist:\n"
                    + " | ".join(colnames)
                )
            else:
                print(f"Error fetching similar values: {e}")
                return f"Error fetching similar values: {e}"
