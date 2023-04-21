# <center>Google Cloud Storage - File Archival on HTTP request

Given a landing, staging and archival path in GCS, the HTTP request to the Cloud Function copies the files from staging to archival and deletes the same file in both staging and landing area. Files are archived inside a folder suffixed with the current datetime.

If there are files only in the staging area and no files are available in the landing area, the function will still successfully archive the files from the staging area.

Please note that the folder containing the files will also be deleted in the process.

#### GCS Bucket Structure

Create a bucket with separate folders for landing, staging, and archival.

gs://file-archival-test/landing/ \
gs://file-archival-test/staging/ \
gs://file-archival-test/archival/

#### Local Test

Run the below command to run the function from your local server.

```shell
mvn clean install function:run -Drun.functionTarget=com.example.cloudstorage_file_archival.CloudStorageFileArchival -Drun.port=1234
```

Use the below URL with the query string parameters passed to send request to the above function.

```
http://localhost:1234/?landingPath=gs%3A%2F%2Ffile-archival-test%2Flanding%2F&stagingPath=gs%3A%2F%2Ffile-archival-test%2Fstaging%2F&archivalPath=gs%3A%2F%2Ffile-archival-test%2Farchival%2F
```

#### Deploy in Cloud Function

Run the below command to deploy in cloud function.

```shell
gcloud functions deploy gcs-file-archival --entry-point com.example.cloudstorage_file_archival.CloudStorageFileArchival --runtime java11 --trigger-http --memory 2GB --allow-unauthenticated
```

Use the below URL with the endpoint modified according to your project to trigger the Cloud Function with HTTP request.

```
https://us-central1-arched-autumn-379510.cloudfunctions.net/gcs-file-archival?landingPath=gs%3A%2F%2Ffile-archival-test%2Flanding%2F&stagingPath=gs%3A%2F%2Ffile-archival-test%2Fstaging%2F&archivalPath=gs%3A%2F%2Ffile-archival-test%2Farchival%2F
```
