# <img src="./images/azure_logo.png" alt="Azure Logo" style="width:30px;height:30px;"/> Azure Open AI Assistant for Natural Language to SQL
# Assistant NL2SQL

Assistant NL2SQL is a natural language processing tool that converts natural language queries into SQL queries. This project aims to simplify database querying for users who may not be familiar with SQL syntax.

## Features

- Convert natural language questions to SQL queries
- Support for PostgreSQL and BigQuery
- User-friendly interface
- High accuracy and performance
- Auto correction given possible errors

## Setup

To setup the project, clone the repository and install the dependencies:

```bash
git clone https://github.com/Azure-Samples/assistant-nl2sql.git
cd assistant-nl2sql

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

1. **From command line:** 
- To use the tool, run the following command (for a postgresql assistant):

```bash
python src/main.py --database postgresql  
```
Then, follow the on-screen instructions to input your natural language query.

- If you want a bigquery assistant, try:
```bash
python src/main.py --database bigquery 
```

2. **Using a streamlit app:**
- To launch the app locally (for bigquery):
```bash
streamlit run app.py
```

## Docker Image
- Build the docker image (for bigquery):
```bash
docker build -t bigassistant-app:latest .
```

- Start the services defined in the [docker-compose](docker-compose.yml)
```bash
docker-compose up
```

## Examples
You can test the assistant with the following examples:

Input:
```
Give me the seller name with the best sales performance
```

Input:
```
Show me the total sales amount for each seller
```


## Infrastructure
You can use the shell script `set_up.sh` to set up the infrastructure on Azure. This script will create a resource group, a storage account, a container, and a PostgreSQL database. To run the script, you need to have the Azure CLI installed and be logged in. You can install the Azure CLI by following the instructions [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).

Please, pay attention to the costs of the resources created by the script. 

- To create resources for the postgresql assistant 
```bash
az login
./set_up.sh run_all postgresql
```

- To create resources for the bigquery assistant:<br>
You must have a service-account saved [inside here](./secrets/). 
For more information [see](https://cloud.google.com/iam/docs/service-accounts-create).

```bash
az login
./set_up.sh run_all bigquery
```

- You can provide [examples](data/examples.csv) of queries that the assistant can use as few shot examples. Those examples will be indexed and available to the assistant through a tool call. The examples should be adapted to the database syntax.

## Supported Databases:

- **PostgreSQL Database**
    We provide a sample PostgreSQL tables that you can use to test the assistant. 

    ```python
    python util/create-sample-database.py
    ```

    - Table's Schema <br>
    ![Schema](./images/tables_structure.png)

- **BigQuery**
    The same schema can be recreated in Google BigQuery for you to test the assistant. 

    ```python
    python util/create-sample-database-bigquery.py
    ```

**Note:** If you ran the shell scripts that create the infrastructure, the data has already been created for you, **NO NEED TO RUN THESE SCRIPTS AGAIN** 

## Contributing

We welcome contributions! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please open an issue on GitHub.