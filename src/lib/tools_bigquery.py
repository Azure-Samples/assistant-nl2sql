from google.cloud import bigquery
from .function import Function, Property
from .config import BigQueryConfig as config


class GetDBSchema(Function):
    def __init__(self):
        super().__init__(
            name="get_db_schema",
            description="Get the schema of the BigQuery dataset",
        )

    def function(self):
        config = config()
        client = bigquery.Client.from_service_account_json(config.service_account_json)
        dataset_ref = client.dataset(config.dataset_id)
        tables = client.list_tables(dataset_ref)

        create_statements = []
        sample_rows_info = ""

        for table in tables:
            table_ref = dataset_ref.table(table.table_id)
            table_obj = client.get_table(table_ref)
            schema = table_obj.schema

            create_statement = f"CREATE TABLE {table.table_id} ("
            column_definitions = []
            for field in schema:
                column_def = f"{field.name} {field.field_type}"
                if field.mode == "REQUIRED":
                    column_def += " NOT NULL"
                column_definitions.append(column_def)

            create_statement += ", ".join(column_definitions) + ");"
            create_statements.append(create_statement)

            # Get sample rows
            limit = 3
            rows = client.list_rows(table_ref, max_results=limit)
            columns_str = "\t".join([field.name for field in schema])
            rows_str = "\n".join(["\t".join(map(str, row.values())) for row in rows])
            sample_rows_info += (
                f"{limit} rows from {table.table_id} table:\n"
                f"{columns_str}\n"
                f"{rows_str}\n\n"
            )

        table_info = (
            f"Dataset is: {config.dataset_id}. You must use it to qualify the tables in your queries (e.g. {config.dataset_id}.table)\n\n"
            + "\n\n".join(create_statements)
            + "\n\n"
            + sample_rows_info
        )

        return table_info


class RunSQLQuery(Function):
    def __init__(self):
        super().__init__(
            name="run_sql_query",
            description="Run a SQL query on the BigQuery dataset",
            parameters=[
                Property(
                    name="query",
                    description="The SQL query to run",
                    type="string",
                    required=True,
                ),
            ],
        )

    def function(self, query):
        try:
            client = bigquery.Client.from_service_account_json(
                config.service_account_json
            )
            query_job = client.query(query)
            results = query_job.result()
            return "\n".join([str(result) for result in results])
        except Exception as e:
            return f"Error running query: {e}"


class ListTables(Function):
    def __init__(self):
        super().__init__(
            name="list_tables",
            description="List the tables in the BigQuery dataset",
        )

    def function(self):
        try:
            client = bigquery.Client.from_service_account_json(
                config.service_account_json
            )
            dataset_ref = client.dataset(config.dataset_id)
            tables = client.list_tables(dataset_ref)
            table_names = [table.table_id for table in tables]
            return "\n".join(table_names)
        except Exception as e:
            return f"Error listing tables: {e}"


class FetchDistinctValues(Function):
    def __init__(self):
        super().__init__(
            name="fetch_distinct_values",
            description="Fetch the first 10 distinct values of a specified column for a certain table",
            parameters=[
                Property(
                    name="dataset_id",
                    description="The dataset id which contains the table",
                    type="string",
                    required=True,
                ),
                Property(
                    name="table_name",
                    description="The table name to fetch distinct values. NOTE: Must not contain the dataset id",
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

    def function(self, dataset_id, table_name, column_name):
        try:
            client = bigquery.Client.from_service_account_json(
                config.service_account_json
            )
            query = f"""
                SELECT {column_name}, COUNT(*) as qty
                FROM `{dataset_id}.{table_name}`
                GROUP BY {column_name}
                ORDER BY qty DESC
                LIMIT 10
            """
            query_job = client.query(query)
            rows = query_job.result()

            colnames = [field.name for field in rows.schema]
            result = " | ".join(colnames) + "\n"
            result += "\n".join([" | ".join(map(str, row.values())) for row in rows])

            return result

        except bigquery.NotFound:
            # If the column is not found, list available columns
            table_ref = client.dataset(config.dataset_id).table(table_name)
            table_obj = client.get_table(table_ref)
            available_columns = [field.name for field in table_obj.schema]
            return f"Column '{column_name}' not found. Available columns: {', '.join(available_columns)}"
        except Exception as e:
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
            client = bigquery.Client.from_service_account_json(
                config.service_account_json
            )

            query = f"""
                SELECT {column_name},
                        ROUND(utility.levenshtein(CAST({column_name} AS STRING), '{value}'),2) AS similarity_score
                FROM `{config.dataset_id}.{table_name}`
                WHERE ROUND(utility.levenshtein(CAST({column_name} AS STRING), '{value}'),2) > 0.3
                ORDER BY similarity_score DESC
                LIMIT 10
            """
            query_job = client.query(query)
            rows = query_job.result()

            if rows.total_rows == 0:
                return f"No similar values found for {value} in {column_name} for table {table_name}"

            colnames = [field.name for field in rows.schema]
            result = " | ".join(colnames) + "\n"
            result += "\n".join([" | ".join(map(str, row.values())) for row in rows])

            return result

        except Exception as e:
            return f"Error fetching similar values: {e}"
