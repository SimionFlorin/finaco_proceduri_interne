from azure.storage.blob import BlobServiceClient
import os

def download_files_from_blob(connection_string, container_name="pdfs", local_download_path="pdfs"):
    """
    Downloads all files from a given Azure Blob Storage container to a local path.

    :param connection_string: The connection string to access Azure Blob Storage
    :param container_name: The name of the container from which to download files (default is "pdfs")
    :param local_download_path: The local path where files will be downloaded (default is "pdfs")
    """
    
    # Create the BlobServiceClient object which will be used to access the container
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Get the container client to access your container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container
    blobs_list = container_client.list_blobs()

    # Ensure the local download directory exists
    if not os.path.exists(local_download_path):
        os.makedirs(local_download_path)

    # Download each blob in the container
    for blob in blobs_list:
        blob_client = container_client.get_blob_client(blob)
        
        # Local path to save the file
        download_file_path = os.path.join(local_download_path, blob.name)

        # Download the blob
        print(f"Downloading {blob.name} to {download_file_path}")
        with open(download_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())

    print("All files downloaded successfully.")
