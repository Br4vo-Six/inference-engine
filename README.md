# Bittrack inference engine
The backend engine for the API and the inference of the model

# Deployment
1. To deploy the engine, a running monggo db server, a dataset for a known bad address from eliptic++, is needed.
2. Then rename the .env.example file into .env file, and modify it as needed for the usecase

# Example environment file
There are 4 sections needed in the .env file, to define the environment variable for the backend.

1. MonggoDB connection definition. This section consist of the URI to the monggoDB server, and the name of the database or table.
2. Known bad addresses. This define the filename and the path for the eliptic++ known transaction list as the initial knowledge used by the model to infer the level of licitness of the wallet addreeses.
3. Scrapper source. This section defines the scrapper algorithm used, whether it is from the bigquery, or the blockcypher. In order to use the bigquery, a modification in `bigquery/scrapper.py` for the name of the table might be required, and the `bigquery/queryWrap.py` requires a modification to point on the correct google cloud platform credential for the bigquery.
4. Model. This section only has one environment variable, which defines the model used for the inference.

# Endpoint routing
## Trust Score
  `/wallet/{address}/trust-score`
  End point to find the trust score from the wallet address
