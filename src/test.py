import os
from google.cloud import bigquery
from dotenv import load_dotenv
from lib.tools_bigquery import GetDBSchema, RunSQLQuery, ListTables, FetchDistinctValues, FetchSimilarValues

def test():
    # Initialize the GetDBSchema function
    # get_db_schema = GetDBSchema()
    # run_sql_query = RunSQLQuery()
    # list_tables = ListTables()
    # fetch_distinct_values = FetchDistinctValues()
    fetch_similar_values = FetchSimilarValues()

    # Call the function method
    # query="""SELECT
    #         p.product_name,
    #         CASE
    #         WHEN p.in_stock THEN 100
    #         ELSE 0
    #         END AS percentage_in_stock
    #     FROM
    #         `demomeli-439613.sales_sample_db.products` AS p
    #     ORDER BY
    #         p.product_name;SELECT
    #         s.seller_name,
    #         AVG(st.quantity) AS average_quantity_per_transaction
    #     FROM
    #         `demomeli-439613.sales_sample_db.sellers` AS s
    #         INNER JOIN `demomeli-439613.sales_sample_db.sales_transaction` AS st ON s.seller_id = st.seller_id
    #     GROUP BY 1
    #     ORDER BY 2
    #     """
    
    print(fetch_similar_values.function('products', 'product_category', 'electro'))

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Run the test
    test()