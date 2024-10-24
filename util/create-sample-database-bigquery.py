import os
import json
import csv
from google.cloud import bigquery
from dotenv import load_dotenv
from faker import Faker
import argparse


class SampleDatabaseCreator:
    def __init__(self):
        load_dotenv(override=True)

        # Load BigQuery json directory path from .env file
        self.keys_dir = os.getenv("SERVICE_ACCOUNT_JSON_PATH")
        project_root = os.path.abspath(os.path.dirname(__file__))
        self.keys_dir = os.path.join(project_root, "..", self.keys_dir)

        # Check if the directory exists
        if not os.path.isdir(self.keys_dir):
            raise NotADirectoryError(
                f"Service account JSON directory not found at {self.keys_dir}"
            )

        # Find the JSON file in the directory
        json_files = [f for f in os.listdir(self.keys_dir) if f.endswith(".json")]
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in directory {self.keys_dir}")

        self.keys_path = os.path.join(self.keys_dir, json_files[0])

        # Open and load the JSON file
        try:
            with open(self.keys_path, "r") as json_file:
                self.keys = json.load(json_file)
        except json.JSONDecodeError:
            raise ValueError(f"File at {self.keys_path} is not a valid JSON file")

        self.client = bigquery.Client.from_service_account_json(self.keys_path)

    def create_dataset_and_tables(self, dataset_name):
        # Create new dataset
        dataset_id = f"{self.client.project}.{dataset_name}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        self.client.create_dataset(dataset, exists_ok=True)

        # Create tables
        schema_products = [
            bigquery.SchemaField("product_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("product_description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("product_price", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("product_category", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("in_stock", "BOOL", mode="REQUIRED"),
        ]
        table_id_products = f"{dataset_id}.products"
        table_products = bigquery.Table(table_id_products, schema=schema_products)
        self.client.create_table(table_products, exists_ok=True)

        schema_sellers = [
            bigquery.SchemaField("seller_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("seller_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("seller_email", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("seller_contact_number", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("seller_address", "STRING", mode="NULLABLE"),
        ]
        table_id_sellers = f"{dataset_id}.sellers"
        table_sellers = bigquery.Table(table_id_sellers, schema=schema_sellers)
        self.client.create_table(table_sellers, exists_ok=True)

        schema_sales_transaction = [
            bigquery.SchemaField("transaction_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("product_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("seller_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("quantity", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("transaction_date", "DATE", mode="REQUIRED"),
        ]
        table_id_sales_transaction = f"{dataset_id}.sales_transaction"
        table_sales_transaction = bigquery.Table(
            table_id_sales_transaction, schema=schema_sales_transaction
        )
        self.client.create_table(table_sales_transaction, exists_ok=True)

    def populate_sample_data(self, dataset_name):
        dataset_id = f"{self.client.project}.{dataset_name}"

        # Create Faker object
        fake = Faker()

        # Insert Products
        products = [
            (
                1,
                "Apple iPhone 13",
                "Latest model of iPhone with A15 Bionic chip",
                999.99,
                "Electronics",
                True,
            ),
            (
                2,
                "Nike Air Force 1",
                "Classic Nike sneakers in white",
                90.00,
                "Footwear",
                True,
            ),
            (3, "The Alchemist", "A novel by Paulo Coelho", 10.99, "Books", True),
            (
                4,
                "Apple iPhone 12",
                "Previous model of iPhone with A14 Bionic chip",
                799.99,
                "Electronics",
                True,
            ),
            (
                5,
                "Adidas Ultraboost",
                "Running shoes with Boost cushioning",
                180.00,
                "Footwear",
                True,
            ),
            (6, "To Kill a Mockingbird", "A novel by Harper Lee", 12.99, "Books", True),
            (
                7,
                "Apple iPhone 11",
                "Older model of iPhone with A13 Bionic chip",
                699.99,
                "Electronics",
                False,
            ),
            (
                8,
                "Vans Old Skool",
                "Classic Vans sneakers in black and white",
                60.00,
                "Footwear",
                True,
            ),
            (9, "1984", "A novel by George Orwell", 9.99, "Books", True),
            (
                10,
                "Samsung Galaxy S21",
                "Latest model of Samsung Galaxy with Exynos 2100 chip",
                899.99,
                "Electronics",
                True,
            ),
        ]
        products_csv_path = os.path.join(os.path.dirname(__file__), "products.csv")
        with open(products_csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "product_id",
                    "product_name",
                    "product_description",
                    "product_price",
                    "product_category",
                    "in_stock",
                ]
            )
            writer.writerows(products)

        table_id_products = f"{dataset_id}.products"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=False,
        )
        with open(products_csv_path, "rb") as source_file:
            job = self.client.load_table_from_file(
                source_file, table_id_products, job_config=job_config
            )
        job.result()  # Wait for the job to complete

        # Insert Sellers
        sellers = [
            (
                1,
                "John Doe",
                "johndoe@example.com",
                "1234567890",
                "123 Main St, Anytown, USA",
            ),
            (
                2,
                "Jane Smith",
                "janesmith@example.com",
                "0987654321",
                "456 High St, Sometown, USA",
            ),
            (
                3,
                "Bob Johnson",
                "bobjohnson@example.com",
                "1122334455",
                "789 Low St, Othertown, USA",
            ),
        ]
        sellers_csv_path = os.path.join(os.path.dirname(__file__), "sellers.csv")
        with open(sellers_csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "seller_id",
                    "seller_name",
                    "seller_email",
                    "seller_contact_number",
                    "seller_address",
                ]
            )
            writer.writerows(sellers)

        table_id_sellers = f"{dataset_id}.sellers"
        with open(sellers_csv_path, "rb") as source_file:
            job = self.client.load_table_from_file(
                source_file, table_id_sellers, job_config=job_config
            )
        job.result()  # Wait for the job to complete

        # Populate sales_transaction table with faker data
        sales_transactions = []
        for i in range(100):
            transaction_id = i + 1
            product_id = fake.random_int(min=1, max=10)
            seller_id = fake.random_int(min=1, max=3)
            quantity = fake.random_int(min=1, max=10)
            transaction_date = fake.date_between(start_date="-3y", end_date="today")
            sales_transactions.append(
                (transaction_id, product_id, seller_id, quantity, transaction_date)
            )

        sales_transactions_csv_path = os.path.join(
            os.path.dirname(__file__), "sales_transactions.csv"
        )
        with open(sales_transactions_csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "transaction_id",
                    "product_id",
                    "seller_id",
                    "quantity",
                    "transaction_date",
                ]
            )
            writer.writerows(sales_transactions)

        table_id_sales_transaction = f"{dataset_id}.sales_transaction"
        with open(sales_transactions_csv_path, "rb") as source_file:
            job = self.client.load_table_from_file(
                source_file, table_id_sales_transaction, job_config=job_config
            )
        job.result()  # Wait for the job to complete

        # Delete the CSV files
        os.remove(products_csv_path)
        os.remove(sellers_csv_path)
        os.remove(sales_transactions_csv_path)

    def query_data(self, dataset_name, table_name):
        query = f"""
        SELECT *
        FROM `{self.client.project}.{dataset_name}.{table_name}`
        LIMIT 10
        """
        query_job = self.client.query(query)

        results = query_job.result()
        for row in results:
            print(dict(row))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create and populate a sample BigQuery database."
    )
    parser.add_argument(
        "dataset_name", type=str, help="The name of the dataset to create."
    )
    args = parser.parse_args()

    dataset_name = args.dataset_name
    creator = SampleDatabaseCreator()

    creator.create_dataset_and_tables(dataset_name)
    creator.populate_sample_data(dataset_name)

    # Query data from the products table
    creator.query_data(dataset_name, "products")
