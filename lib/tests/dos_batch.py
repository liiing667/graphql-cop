"""Batch tests."""
from lib.utils import build_headers, graph_query, process_response


def batch_query(url, proxy, headers, debug_mode):
  """Check for batch queries."""
  res = {
    'result':False,
    'title':'Array-based Query Batching',
    'description':'Batch queries allowed with 10+ simultaneous queries',
    'impact':'Denial of Service - /' + url.rsplit('/', 1)[-1],
    'severity':'HIGH',
    'color': 'red',
    'curl_verify':'',
    'error':None
  }

  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload='query cop { __typename }', batch=True)
  body = process_response(res, gql_response)

  try:
      if body and len(body) >= 10:
        res['result'] = True
  except Exception:
    pass

  return res
