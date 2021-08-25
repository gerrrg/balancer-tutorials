# basics
import json
import math
import sys

# thegraph queries
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

num_pools_to_query = 20

# Initialize subgraph
subgraph_url = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
balancer_transport=RequestsHTTPTransport(
    url=subgraph_url,
    verify=True,
    retries=3
)
client = Client(transport=balancer_transport)

query_string = '''
query {{
  pools(first: {first}, skip: {skip}) {{
    id
    address
    poolType
    strategyType
    swapFee
    amp
  }}
}}
'''
formatted_query_string = query_string.format(first=num_pools_to_query, skip=0)
response = client.execute(gql(formatted_query_string))

for pool in response["pools"]:
	pool_token_query = '''
	query {{
	  poolTokens(first: 8, where: {{ poolId: "{pool_id}" }}) {{
	    id
		symbol
		name
		decimals
		address
		balance
		invested
		investments
		weight
	  }}
	}}
	''';
	formatted_query_string = pool_token_query.format(pool_id=pool["id"])
	token_response = client.execute(gql(formatted_query_string))
	pool["poolTokens"] = token_response["poolTokens"]

print(json.dumps(response["pools"], indent=4))