import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from faker import Faker


class SampleDatabaseCreator:
    def __init__(self):
        load_dotenv(override=True)

        self.db_params = {
            "user": f"{os.getenv('AZURE_POSTGRES_USER')}",
            "password": os.getenv("AZURE_POSTGRES_PASSWORD"),
            "host": f"{os.getenv('AZURE_POSTGRES_SERVER')}"
            + ".postgres.database.azure.com",
            "port": 5432,
            "sslmode": "require",
        }
        self.verbose = True

        # Connect to PostgreSQL server
        self.conn = psycopg2.connect(
            dbname="postgres",
            user=self.db_params["user"],
            password=self.db_params["password"],
            host=self.db_params["host"],
            port=self.db_params["port"],
            sslmode=self.db_params["sslmode"],
        )

        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def create_database_and_tables(self, database_name):
        # Create new database
        self.cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
        self.cursor.execute(f"CREATE DATABASE {database_name}")

        # Close the connection to the default database
        self.cursor.close()
        self.conn.close()

        # Connect to the new database
        self.conn = psycopg2.connect(
            dbname=database_name,
            user=self.db_params["user"],
            password=self.db_params["password"],
            host=self.db_params["host"],
            port=self.db_params["port"],
            sslmode=self.db_params["sslmode"],
        )

        self.cursor = self.conn.cursor()

        # Create tables
        create_products_table = f"""
        CREATE TABLE products (
            product_id INT PRIMARY KEY,
            product_name VARCHAR(100),
            product_description TEXT,
            product_price DECIMAL(10, 2),
            product_category VARCHAR(50),
            in_stock BIT
        );
        """

        create_sellers_table = f"""
        CREATE TABLE sellers (
            seller_id INT PRIMARY KEY,
            seller_name VARCHAR(100),
            seller_email VARCHAR(100),
            seller_contact_number VARCHAR(15),
            seller_address TEXT
        );
        """

        create_sales_transaction_table = f"""
        CREATE TABLE sales_transaction (
            transaction_id INT PRIMARY KEY,
            product_id INT,
            seller_id INT,
            quantity INT,
            transaction_date DATE,
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
        );
        """

        self.cursor.execute(create_products_table)
        self.cursor.execute(create_sellers_table)
        self.cursor.execute(create_sales_transaction_table)

        # Commit changes and close connection
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def populate_sample_data(self, database_name):

        # Connect to the new database
        self.conn = psycopg2.connect(
            dbname=database_name,
            user=self.db_params["user"],
            password=self.db_params["password"],
            host=self.db_params["host"],
            port=self.db_params["port"],
            sslmode=self.db_params["sslmode"],
        )

        self.cursor = self.conn.cursor()

        # Clean up the database
        self.cursor.execute("DELETE FROM sales_transaction")
        self.cursor.execute("DELETE FROM products")
        self.cursor.execute("DELETE FROM sellers")

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
                1,
            ),
            (
                2,
                "Nike Air Force 1",
                "Classic Nike sneakers in white",
                90.00,
                "Footwear",
                1,
            ),
            (3, "The Alchemist", "A novel by Paulo Coelho", 10.99, "Books", 1),
            (
                4,
                "Apple iPhone 12",
                "Previous model of iPhone with A14 Bionic chip",
                799.99,
                "Electronics",
                1,
            ),
            (
                5,
                "Adidas Ultraboost",
                "Running shoes with Boost cushioning",
                180.00,
                "Footwear",
                1,
            ),
            (6, "To Kill a Mockingbird", "A novel by Harper Lee", 12.99, "Books", 1),
            (
                7,
                "Apple iPhone 11",
                "Older model of iPhone with A13 Bionic chip",
                699.99,
                "Electronics",
                0,
            ),
            (
                8,
                "Vans Old Skool",
                "Classic Vans sneakers in black and white",
                60.00,
                "Footwear",
                1,
            ),
            (9, "1984", "A novel by George Orwell", 9.99, "Books", 1),
            (
                10,
                "Samsung Galaxy S21",
                "Latest model of Samsung Galaxy with Exynos 2100 chip",
                899.99,
                "Electronics",
                1,
            ),
        ]
        for product in products:
            self.cursor.execute(
                "INSERT INTO products (product_id, product_name, product_description, product_price, product_category, in_stock) \
                    VALUES (%s, %s, %s, %s, %s, %s::bit)",
                product,
            )

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
        for seller in sellers:
            self.cursor.execute(
                "INSERT INTO sellers (seller_id, seller_name, seller_email, seller_contact_number, seller_address) \
                    VALUES (%s, %s, %s, %s, %s)",
                seller,
            )

        # Populate sales_transaction table with faker data
        for i in range(100):
            # Generate fake data
            transaction_id = i + 1
            product_id = fake.random_int(min=1, max=3)
            seller_id = fake.random_int(min=1, max=3)
            quantity = fake.random_int(min=1, max=10)
            transaction_date = fake.date_between(start_date="-3y", end_date="today")

            self.cursor.execute(
                "INSERT INTO sales_transaction (transaction_id, product_id, seller_id, quantity, transaction_date) \
                    VALUES (%s, %s, %s, %s, %s)",
                (transaction_id, product_id, seller_id, quantity, transaction_date),
            )

        # Commit changes and close connection
        self.conn.commit()
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    database_name = "sales_sample_db"
    creator = SampleDatabaseCreator()

    creator.create_database_and_tables(database_name)
    creator.populate_sample_data(database_name)
