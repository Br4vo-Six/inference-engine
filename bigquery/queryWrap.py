"""queryWrap
Wrapper for all of google bigquery API operation"""

from google.cloud import bigquery
from google.oauth2 import service_account


key_path = "../bravo-six_query_credential.json"

def send_query(query: str) -> str:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    query_job = client.query(query)  # Make the API request.
    return [dict(row) for row in query_job]
