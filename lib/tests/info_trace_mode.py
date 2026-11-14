"""Collect trace mode details."""
from lib.utils import build_headers, graph_query, process_response


def trace_mode(url, proxy, headers, debug_mode):
  """Get the trace mode."""
  res = {
    'result':False,
    'title':'Trace Mode',
    'description':'Tracing is Enabled',
    'impact':'Information Leakage - /' + url.rsplit('/', 1)[-1],
    'severity':'INFO',
    'color': 'green',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop { __typename }'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload=q)
  body = process_response(res, gql_response)
  try:
    if body and body['errors'][0]['extensions']['tracing']:
      res['result'] = True
    elif body and "'extensions': {'tracing':" in str(body).lower():
      res['result'] = True
  except Exception:
    pass

  return res
