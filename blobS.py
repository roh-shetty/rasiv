from azure.storage.blob import BlobServiceClient
import pandas as pd

# Azure Blob Storage connection details
account_name = 'your_storage_account_name'
account_key = 'your_storage_account_key'
container_name = 'your_container_name'
blob_name = 'your_blob_name'

# Create a DataFrame to append
new_data = pd.DataFrame({'Column1': [1, 2, 3], 'Column2': ['A', 'B', 'C']})

# Convert the DataFrame to CSV format
csv_data = new_data.to_csv(index=False)

# Create a connection to Azure Blob Storage
conn_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(conn_str)
container_client = blob_service_client.get_container_client(container_name)

# Check if the blob exists, and if not, create it with the CSV data
if not container_client.exists_blob(blob_name):
    container_client.upload_blob(name=blob_name, data=csv_data)
else:
    # Append the CSV data to the existing blob
    existing_data = container_client.get_blob_client(blob_name).download_blob().content_as_text()
    appended_data = existing_data + '\n' + csv_data
    container_client.get_blob_client(blob_name).upload_blob(data=appended_data, overwrite=True)
