"""Perform introspection tests."""
from lib.utils import build_headers, graph_query, process_response


def introspection(url, proxy, headers, debug_mode):
  """Run introspection."""
  res = {
    'result':False,
    'title':'Introspection',
    'description':'Introspection Query Enabled',
    'impact':'Information Leakage - /' + url.rsplit('/', 1)[-1],
    'severity':'HIGH',
    'color': 'red',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop { __schema { types { name fields { name } } } }'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload=q)
  body = process_response(res, gql_response)
  try:
    if body and body['data']['__schema']['types']:
      res['result'] = True
  except Exception:
    pass

  return res
