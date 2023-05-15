import os
import pandas as pd
import numpy as np
from google.cloud import bigquery


"""

Author: Mageshkumar N

Usage: 

Import the module bq_load_data and call the function load_data_to_bq() by overwriting the default keyword arguements table_name and input_file.

It will accommodate the dynamic schema changes from the input file. 

For example, if there are additional columns in the input file than those expected in the BigQuery table, those columns will be created in BQ. Similarly, if the column present in BQ table is not available in the input file, the column will be created in the input dataframe with null values before loading to BQ. 

Assumption: 

BigQuery Table is already created and available.

"""


# Reading Input CSV file into Dataframe

def get_pd_dataframe (input_file):
    
    df = pd.read_csv(input_file)
    return df


# Fetching BQ Table

def get_bq_table (project_id, service_account_key_location, service_account_key_name, table_name):
    
    os.system('gsutil -m -o GSUtil:parallel_composite_upload_threshold=150M cp -r ' 
          + service_account_key_location + service_account_key_name + ' .')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_name
    
    client = bigquery.Client.from_service_account_json(service_account_key_name, project=project_id)
    table = client.get_table(table_name)
    
    return (client, table)
    


# Updating BigQuery schema based on the input file schema

def update_bq_table_schema (project_id, service_account_key_location, service_account_key_name, table_name, input_file):
    
    client, table = get_bq_table(project_id, service_account_key_location, service_account_key_name, table_name)
    df = get_pd_dataframe(input_file)

    df_columns = list(df.columns)
    bq_columns = [schema.name for schema in table.schema]

    new_cols = list(set(df_columns) - set(bq_columns))
    
    if len(new_cols) != 0:
        print('List of new columns from the input file: ', new_cols)
        new_schema = table.schema

        # Schema is inferred according to the document https://pandas-gbq.readthedocs.io/en/latest/writing.html#inferring-the-table-schema

        for new_col in new_cols:
            if (df[new_col].dtype.kind.startswith('O') or 
                df[new_col].dtype.kind.startswith('S') or 
                df[new_col].dtype.kind.startswith('U')):
                print(f'Adding the column {new_col} with type STRING to the BQ Schema')
                new_schema.append(bigquery.SchemaField(new_col, 'STRING'))

            elif df[new_col].dtype.kind.startswith('i'):
                print(f'Adding the column {new_col} with type INTEGER to the BQ Schema')
                new_schema.append(bigquery.SchemaField(new_col, 'INTEGER'))

            elif df[new_col].dtype.kind.startswith('f'):
                print(f'Adding the column {new_col} with type FLOAT to the BQ Schema')
                new_schema.append(bigquery.SchemaField(new_col, 'FLOAT'))

            elif df[new_col].dtype.kind.startswith('b'):
                print(f'Adding the column {new_col} with type BOOLEAN to the BQ Schema')
                new_schema.append(bigquery.SchemaField(new_col, 'BOOLEAN'))

            elif df[new_col].dtype.kind.startswith('M'):
                print(f'Adding the column {new_col} with type TIMESTAMP to the BQ Schema')
                new_schema.append(bigquery.SchemaField(new_col, 'TIMESTAMP'))

        table.schema = new_schema
        client.update_table(table, ['schema'])
        print(f'New Columns {new_cols} are added to the BigQuery Table')
        
    return (df, table)


# Casting pandas datatypes to the BigQuery datatypes

def cast_dtypes_to_bq (df, table):
    
    df_columns = list(df.columns)
    bq_columns = [schema.name for schema in table.schema]
    
    new_cols = list(set(df_columns) - set(bq_columns))
    deleted_cols = list(set(bq_columns) - set(df_columns))
    
    if len(new_cols) == 0:
        
        if len(deleted_cols) != 0:
            print(f'List of columns that are not available in the input file for loading: {deleted_cols}')
            
        """
        If the column present in Dataframe is not available in BigQuery, it'll be dropped.
        If the column present in BigQuery is not available in Dataframe, the same will be created in the Dataframe.
        """
        df = df.reindex(columns=bq_columns)
        
    # Schema is inferred according to the document https://pandas-gbq.readthedocs.io/en/latest/writing.html#inferring-the-table-schema

    bq_schema = [schema.to_api_repr() for schema in table.schema]

    for bq_col in bq_schema:
        
        if bq_col['type'] == 'STRING':
            df[bq_col['name']] = df[bq_col['name']].astype(pd.StringDtype())
            
        elif bq_col['type'] == 'INTEGER':
            df[bq_col['name']] = df[bq_col['name']].astype(pd.Int64Dtype())
            
        elif bq_col['type'] == 'FLOAT':
            df[bq_col['name']] = df[bq_col['name']].astype(pd.Float64Dtype())
            
        elif bq_col['type'] == 'BOOLEAN':
            df[bq_col['name']] = df[bq_col['name']].astype(pd.BooleanDtype())
            
        elif bq_col['type'] == 'TIMESTAMP':
            df[bq_col['name']] = df[bq_col['name']].astype(np.dtype('datetime64[ns]'))
            
    return df
        


# Loading the Data into BigQuery

def load_data_to_bq (project_id='arched-autumn-379510',
                     service_account_key_location='gs://data_engineering/credentials/service_accounts/',
                     service_account_key_name='bq_load_data.json',
                     table_name = 'arched-autumn-379510.TEST.BQ_LOAD_DATA_TEST',
                     input_file = 'test.csv'):

    """

    Input Parameters:
    
    project_id: GCP Project ID where the BigQuery table is located.
    service_account_key_location: Path where the Service Account's Private Key in JSON format is located. 
    service_account_key_name: Service Account's JSON key file to authorize access for the given GCP Project. 
    table_name: BigQuery Table's Name to which the data must be loaded.
    input_file: Absolute path to the input CSV file containing the data to be loaded.

    """
    
    df, table = update_bq_table_schema(project_id, service_account_key_location, service_account_key_name, table_name, input_file)
    df = cast_dtypes_to_bq(df, table)  
    
    client, _ = get_bq_table(project_id, service_account_key_location, service_account_key_name, table_name)
                  
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    
    job = client.load_table_from_dataframe(df, table_name, job_config=job_config)
    job.result()
    
    print('Data from the input file is loaded successfully in BigQuery')
