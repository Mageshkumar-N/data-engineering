package com.example.cloudstorage_file_archival;

import java.text.SimpleDateFormat;
import java.util.Date;

import org.apache.beam.sdk.extensions.gcp.util.gcsfs.GcsPath;

import com.google.cloud.functions.HttpFunction;
import com.google.cloud.functions.HttpRequest;
import com.google.cloud.functions.HttpResponse;
import com.google.cloud.storage.Blob;
import com.google.cloud.storage.BlobId;
import com.google.cloud.storage.BlobInfo;
import com.google.cloud.storage.Bucket;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;

/**
 * 
 * @author Mageshkumar N (mn@equinix.com)
 * 
 * @apiNote A HTTP(S) triggered Cloud Function to archive the files in Cloud
 *          Storage from staging and landing area.
 *
 */

public class CloudStorageFileArchival implements HttpFunction {

	@Override
	public void service(HttpRequest request, HttpResponse response) throws Exception {

		String landingPath = null;
		String stagingPath = null;
		String archivalPath = null;

		try {

			// Fetching the Query String Parameters.
			
			if (request.getFirstQueryParameter("landingPath").isPresent()) {

				landingPath = request.getFirstQueryParameter("landingPath").get();

			}

			if (request.getFirstQueryParameter("stagingPath").isPresent()) {

				stagingPath = request.getFirstQueryParameter("stagingPath").get();

			}

			if (request.getFirstQueryParameter("archivalPath").isPresent()) {

				archivalPath = request.getFirstQueryParameter("archivalPath").get();
			}

			if (request.getFirstQueryParameter("landingPath").isEmpty()
					|| request.getFirstQueryParameter("stagingPath").isEmpty()
					|| request.getFirstQueryParameter("archivalPath").isEmpty()) {

				System.out.println("Mandatory query string parameters are missing.");

				response.setStatusCode(400);

				response.getWriter().write("Mandatory query string parameters are missing.");

			}

			System.out.println("Landing Path: " + landingPath + " Staging Path: " + stagingPath + " Archival Path: "
					+ archivalPath);

			Storage storage = StorageOptions.getDefaultInstance().getService();

			if (landingPath != null && stagingPath != null && archivalPath != null) {

				archiveFile(storage, landingPath, stagingPath, archivalPath, response);

			}

		} catch (Exception e) {

			System.out.println("Archival Failed: " + e.toString());

			response.setStatusCode(400);

			response.getWriter().write("Error while archiving the files. " + e.getMessage());

		}

	}

	public void archiveFile(Storage storage, String landingPath, String stagingPath, String archivalPath,
			HttpResponse response) throws Exception {

		String archivalBucketURL = createArchivalFolder(storage, archivalPath, response);

		copyFilesToArchive(storage, landingPath, stagingPath, archivalBucketURL, response);

	}

	public String createArchivalFolder(Storage storage, String archivalPath, HttpResponse response) throws Exception {

		GcsPath archivalGcsPath = GcsPath.fromUri(archivalPath);

		String archivalBucketName = archivalGcsPath.getBucket();

		String archivalFolderPath = archivalGcsPath.getObject().endsWith("/") ? archivalGcsPath.getObject()
				: archivalGcsPath.getObject() + "/";

		String currentDate = new SimpleDateFormat("ddMMMMyyyy_hhmmss").format(new Date());

		archivalFolderPath += currentDate + "/";

		System.out.println("Archival Folder: " + archivalFolderPath);

		Bucket archivalBucket = null;

		if (storage.get(archivalBucketName) != null) {

			archivalBucket = storage.get(archivalBucketName);

		} else {

			System.out.println("Archival Bucket Not Found.");

			response.setStatusCode(400);

			response.getWriter().write("Archival Bucket Not Found.");

		}

		// Creating a new folder to archive the files.
		
		if (archivalBucket.get(archivalFolderPath) == null) {

			BlobInfo blobInfo = BlobInfo.newBuilder(BlobId.of(archivalBucketName, archivalFolderPath)).build();

			storage.create(blobInfo);

		}

		String archivalBucketURL = "gs://" + archivalBucketName + "/" + archivalFolderPath;

		return archivalBucketURL;

	}

	public void copyFilesToArchive(Storage storage, String landingPath, String stagingPath, String archivalBucketURL,
			HttpResponse response) throws Exception {

		GcsPath stagingGcsPath = GcsPath.fromUri(stagingPath);

		String stagingBucketName = stagingGcsPath.getBucket();

		String stagingFolderPath = stagingGcsPath.getObject().endsWith("/") ? stagingGcsPath.getObject()
				: stagingGcsPath.getObject() + "/";

		if (storage.get(stagingBucketName) != null) {
			
			// Fetching the list of files from the staging area. The method also returns the folder as a blob along with its files. 

			Iterable<Blob> blobs = storage.list(stagingBucketName, Storage.BlobListOption.prefix(stagingFolderPath))
					.iterateAll();

			for (Blob blob : blobs) {

				String stagingBlobName = blob.getName();

				String stagingFileName = stagingBlobName.substring(stagingBlobName.lastIndexOf('/') + 1);

				System.out.println("Staging File Name: " + stagingFileName);

				GcsPath archivalFileURL = GcsPath.fromUri(archivalBucketURL + stagingFileName);

				Storage.CopyRequest copyRequest = Storage.CopyRequest.newBuilder().setSource(blob.getBlobId())
						.setTarget(BlobId.of(archivalFileURL.getBucket(), archivalFileURL.getObject())).build();
				
				// Proceeding with archival only if the BlobID doesn't correspond to the staging folder.

				if (!blob.getName().endsWith("/") && blob.getSize() != 0) {

					storage.copy(copyRequest);

					deleteProcessedFiles(storage, landingPath, blob, stagingFileName, response);

				}

			}
		} else {

			System.out.println("Staging Bucket Not Found.");

			response.setStatusCode(400);

			response.getWriter().write("Staging Bucket Not Found.");

		}

	}

	public void deleteProcessedFiles(Storage storage, String landingPath, Blob blob, String stagingFileName,
			HttpResponse response) throws Exception {

		GcsPath landingGcsPath = GcsPath.fromUri(landingPath);

		String landingBucketName = landingGcsPath.getBucket();

		String landingFolderPath = landingGcsPath.getObject().endsWith("/") ? landingGcsPath.getObject()
				: landingGcsPath.getObject() + "/";

		String landingBlobName = landingFolderPath + stagingFileName;

		BlobId landingBlobId = BlobId.of(landingBucketName, landingBlobName);

		Bucket landingBucket = null;

		if (storage.get(landingBucketName) != null) {

			landingBucket = storage.get(landingBucketName);

		} else {

			System.out.println("Landing Bucket Not Found.");

			response.setStatusCode(400);

			response.getWriter().write("Landing Bucket Not Found.");

		}
		
		// Deleting the file from landing area only if the same is available in the staging area.

		if (landingBucket.get(landingBlobName) != null) {

			storage.delete(landingBlobId);

		}

		blob.delete();

	}

}