from google.cloud import bigquery
from google.oauth2 import service_account
from decimal import Decimal
from datetime import datetime
import json

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()  # Converts datetime to ISO 8601 string format
        return super(CustomEncoder, self).default(obj)

# Path to your service account key file
key_path = "../bravo-six_query_credential.json"

# Load the service account credentials
credentials = service_account.Credentials.from_service_account_file(key_path)

# Initialize a BigQuery client with the credentials
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Your SQL query
walletAddress = "1jTZx9AahJVd3UJHXZpaogkyXLkL2mGvJ"
query = f"""
WITH
  `inp_addr` AS(
  SELECT
    `address`,
    `mtab`.`hash`,
    `inp`.`value`
  FROM
    `bravo-six-428908.bitcoin_data.transactions` AS `mtab`,
    UNNEST(`mtab`.`inputs`) `inp`,
    UNNEST(`inp`.`addresses`) AS `address`
    WHERE
    `address` = "{walletAddress}"
     ),
  `out_addr` AS(
  SELECT
    `address`,
    `mtab`.`hash`,
    `out`.`value`
  FROM
    `bravo-six-428908.bitcoin_data.transactions` AS `mtab`,
    UNNEST(`mtab`.`outputs`) `out`,
    UNNEST(`out`.`addresses`) AS `address`
    WHERE
     `address` = "{walletAddress}"
    ),
`joined_table` AS (
  SELECT
  `inp`.`value` AS `inp_val`,
  `out`.`value` AS `out_val`
  FROM
    `inp_addr` AS `inp`
INNER JOIN
  `out_addr` AS `out`
ON
  `inp`.`address` = `out`.`address`
),
    `unionized_table` AS (
      SELECT `address`,
      ARRAY_AGG(DISTINCT `hash`) AS `tx`
FROM (
    SELECT `address`, `hash` FROM `inp_addr`
    UNION DISTINCT
    SELECT `address`, `hash` FROM `out_addr`
)
GROUP BY
`address`
    ),

    `aggr_data` AS (
      SELECT
      SUM(`join`.`inp_val`) AS `total_received`,
  SUM(`join`.`out_val`) AS `total_sent`,
  SUM(`join`.`inp_val`) - SUM(`join`.`out_val`) AS `balance`
  FROM `joined_table` AS `join`
  ),
`prep_mtab` AS (
  SELECT
    `mtab`.`hash` AS `tx_hash`,
    `mtab`.`block_hash`,
    ARRAY_LENGTH(`mtab`.`inputs`) AS `tx_input_n`,
    ARRAY_LENGTH(`mtab`.`outputs`)AS `tx_output_n`,
    (SELECT sum(`value`) from UNNEST(`inputs`)) as `value`,
    `mtab`.`block_timestamp` AS `confirmed`
    FROM
    `bravo-six-428908.bitcoin_data.transactions` AS `mtab`,
    UNNEST(`mtab`.`inputs`) AS `minp`
)


SELECT
  `uni`.`address` AS `address`,
  `aggr`.*,
  ARRAY_LENGTH(`uni`.`tx`) AS `n_tx`,
  ARRAY(SELECT AS STRUCT *
  FROM UNNEST(`uni`.`tx`) `tx`,
  `prep_mtab` AS `mtab`
  WHERE `mtab`.`tx_hash` = `tx`)
  AS `txrefs`
  FROM
`unionized_table` AS `uni`,
`aggr_data` AS `aggr`
"""

# Run the query and get the result
query_job = client.query(query)  # Make an API request.

# Convert the result to a list of dictionaries
result = [dict(row) for row in query_job]


# Convert the result to JSON
result_json = json.dumps(result, indent=2, cls=CustomEncoder)

# Print the JSON result
print(result_json)
