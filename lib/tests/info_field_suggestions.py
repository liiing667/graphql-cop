"""Field suggestions tests."""
from lib.utils import build_headers, graph_query, get_error, process_response


def field_suggestions(url, proxy, headers, debug_mode):
  """Retrieve field suggestions."""
  res = {
    'result':False,
    'title':'Field Suggestions',
    'description':'Field Suggestions are Enabled',
    'impact':'Information Leakage - /' + url.rsplit('/', 1)[-1],
    'severity':'LOW',
    'color': 'blue',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop { __schema { directive } }'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload=q)
  body = process_response(res, gql_response)

  try:
    if body and 'Did you mean' in get_error(body):
      res['result'] = True
  except Exception:
    pass

  return res
