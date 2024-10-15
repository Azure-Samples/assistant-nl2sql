#!/bin/bash

prefix="demoaiassistant"
location="eastus2"

subscription_id=$(az account show --query id --output tsv)
user_id=$(az ad signed-in-user show --query id --output tsv)

ai_resource_name="$prefix"
ai_resource_name_resource_group_name=$ai_resource_name"-rg"
ai_resource_name_hub_name=$ai_resource_name"-hub"
ai_resource_project_name=$ai_resource_name"-project"
ai_resource_ai_service=$ai_resource_name"-aiservice"
db_server_name="${prefix}pgserver"
db_name="${prefix}database"
db_user="${prefix}user"
db_password=$(openssl rand -base64 12)

function create_resource_group() {
    echo "Creating resource group: $ai_resource_name_resource_group_name"
    az group create --name $ai_resource_name_resource_group_name --location $location > null
}

function create_hub() {
    echo "Creating AI Studio Hub: $ai_resource_name_hub_name"
    az ml workspace create --kind hub --resource-group $ai_resource_name_resource_group_name --name $ai_resource_name_hub_name > null
}

function create_project() {
    hub_id=$(az ml workspace show -g $ai_resource_name_resource_group_name --name $ai_resource_name_hub_name --query id --output tsv)
    echo "Creating AI Studio Project: $ai_resource_project_name"
    az ml workspace create --kind project --resource-group $ai_resource_name_resource_group_name --name $ai_resource_project_name --hub-id $hub_id > null
}

function create_ai_service() {
    echo "Creating AI Service Account: $ai_resource_ai_service"
    az cognitiveservices account purge -l $location -n $ai_resource_ai_service -g $ai_resource_name_resource_group_name
    az cognitiveservices account create --kind AIServices --location $location --name $ai_resource_ai_service --resource-group $ai_resource_name_resource_group_name --sku S0 --yes > null
}

function deploy_models() {
    echo "Deploying GPT-4o"
    az cognitiveservices account deployment create --name $ai_resource_ai_service --resource-group $ai_resource_name_resource_group_name --deployment-name "gpt-4o" --model-name "gpt-4o" --model-version "2024-05-13" --model-format "OpenAI" --sku-capacity "1" --sku-name "Standard" --capacity "100"

    echo "Deploying GPT-4"
    az cognitiveservices account deployment create --name $ai_resource_ai_service --resource-group $ai_resource_name_resource_group_name --deployment-name "gpt-4" --model-name "gpt-4" --model-format "OpenAI" --model-version "turbo-2024-04-09" --sku-capacity "1" --sku-name "GlobalStandard" --capacity "40"

    echo "Deploying Text-embedding-ada-002"
    az cognitiveservices account deployment create --name $ai_resource_ai_service --resource-group $ai_resource_name_resource_group_name --deployment-name "text-embedding-ada-002" --model-name "text-embedding-ada-002" --model-format "OpenAI" --model-version "2" --sku-capacity "1" --sku-name "Standard" --capacity "20"
}

function add_connection_to_hub() {
    echo "Adding AI Service Connection to the HUB"
    ai_service_resource_id=$(az cognitiveservices account show --name $ai_resource_ai_service --resource-group $ai_resource_name_resource_group_name --query id --output tsv)
    ai_service_api_key=$(az cognitiveservices account keys list --name $ai_resource_ai_service --resource-group $ai_resource_name_resource_group_name --query key1 --output tsv)

    rm connection.yml
    echo "name: $ai_resource_ai_service" >> connection.yml
    echo "type: azure_ai_services" >> connection.yml
    echo "endpoint: https://$location.api.cognitive.microsoft.com/" >> connection.yml
    echo "api_key: $ai_service_api_key" >> connection.yml
    echo "ai_services_resource_id:  $ai_service_resource_id" >> connection.yml

    az ml connection create --file connection.yml --resource-group $ai_resource_name_resource_group_name --workspace-name $ai_resource_name_hub_name > null
    rm connection.yml
    az role assignment create --role "Storage Blob Data Contributor" --scope subscriptions/$subscription_id/resourceGroups/$ai_resource_name_resource_group_name --assignee-principal-type User --assignee-object-id $user_id
}

function create_postgresql() {
    echo "Creating PostgreSQL database"
    az postgres server create --resource-group $ai_resource_name_resource_group_name --name $db_server_name --location $location --admin-user $db_user --admin-password $db_password --sku-name B_Gen5_1
    az postgres db create --resource-group $ai_resource_name_resource_group_name --server-name $db_server_name --name $db_name

    current_ip=$(curl -s4 ifconfig.me)
    az postgres server firewall-rule create --resource-group $ai_resource_name_resource_group_name --server-name $db_server_name --name AllowMyIP --start-ip-address $current_ip --end-ip-address $current_ip

    fqdn=$(az postgres server show --resource-group $ai_resource_name_resource_group_name --name $db_server_name --query "fullyQualifiedDomainName" --output tsv)
    connection_string="postgres://$db_user:$db_password@$fqdn:5432/$db_name"

    echo "Creating .env file"
    echo "# Please do not share this file, or commit this file to the repository" > .env
    echo "# This file is used to store the environment variables for the project for demos and testing only" >> .env
    echo "# delete this file when done with demos, or if you are not using it" >> .env
    echo "AZURE_OPENAI_ENDPOINT=https://$location.api.cognitive.microsoft.com/" >> .env
    echo "AZURE_OPENAI_KEY=$ai_service_api_key" >> .env
    echo 'AZURE_OPENAI_API_VERSION="2024-05-01-preview"' >> .env
    echo 'AZURE_OPENAI_MODEL_NAME="gpt-4o"' >> .env
    echo 'AZURE_OPENAI_EMBEDDING_MODEL_NAME="text-embedding-ada-002"' >> .env
    echo "AZURE_POSTGRES_SERVER=$db_server_name" >> .env
    echo "AZURE_POSTGRES_DATABASE=$db_name" >> .env
    echo "AZURE_POSTGRES_USER=$db_user" >> .env
    echo "AZURE_POSTGRES_PASSWORD=$db_password" >> .env
    echo "AZURE_POSTGRES_CONNECTION_STRING=$connection_string" >> .env
    echo "AZURE_SUBSCRIPTION_ID=$subscription_id" >> .env
    echo "AZURE_RESOURCE_GROUP=$ai_resource_name_resource_group_name" >> .env
}

function load_data() {
    echo "Loading data"
    python src/utils/load_data.py
}

function run_all() {
    create_resource_group
    create_hub
    create_project
    create_ai_service
    deploy_models
    add_connection_to_hub
    create_postgresql
    load_data
}

case $1 in
    create_resource_group)
        create_resource_group
        ;;
    create_hub)
        create_hub
        ;;
    create_project)
        create_project
        ;;
    create_ai_service)
        create_ai_service
        ;;
    deploy_models)
        deploy_models
        ;;
    add_connection_to_hub)
        add_connection_to_hub
        ;;
    create_postgresql)
        create_postgresql
        ;;
    load_data)
        load_data
        ;;
    run_all)
        run_all
        ;;
    *)
        echo "Usage: $0 {create_resource_group|create_hub|create_project|create_ai_service|deploy_models|add_connection_to_hub|create_postgresql|load_data|query_data|run_all}"
        exit 1
        ;;
esac