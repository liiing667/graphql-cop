"""Perform Circular Query based on Introspection."""
from lib.utils import build_headers, graph_query, process_response

def circular_query_introspection(url, proxy, headers, debug_mode):
  """Run a Circular Query using introspection."""
  res = {
    'result':False,
    'title':'Introspection-based Circular Query',
    'description':'Circular-query using Introspection',
    'impact':'Denial of Service - /' + url.rsplit('/', 1)[-1],
    'severity':'HIGH',
    'color': 'red',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop { __schema { types { fields { type { fields { type { fields { type { fields { type { name } } } } } } } } } } }'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload=q)
  body = process_response(res, gql_response)
  try:
    if body and len(body['data']['__schema']['types']) > 25:
      res['result'] = True
  except Exception:
    pass

  return res
