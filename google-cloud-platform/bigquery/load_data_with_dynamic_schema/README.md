# <center> Loading Dynamic Data into BigQuery

### Usage

Import the module bq_load_data and call the function load_data_to_bq() by overwriting the default keyword arguements table_name and input_file.

It will accommodate the dynamic schema changes from the input file. 

For example, if there are additional columns in the input file than those expected in the BigQuery table, those columns will be created in BQ. Similarly, if the column present in BQ table is not available in the input file, the column will be created in the input dataframe with null values before loading to BQ. 

**Assumption:** BigQuery Table is already created and available.

### Input Parameters Required

* **project_id:** GCP Project ID where the BigQuery table is located.
* **service_account_key_location:** Path where the Service Account's Private Key in JSON format is located. 
* **service_account_key_name:** Service Account's JSON key file to authorize access for the given GCP Project. 
* **table_name:** BigQuery Table's Name to which the data must be loaded.
* **input_file:** Absolute path to the input CSV file containing the data to be loaded.
