"""Collect GraphiQL details."""
from lib.utils import build_headers, process_response, request

def detect_graphiql(url, proxy, headers, debug_mode):
  """Get GraphiQL."""
  res = {
    'result':False,
    'title':'GraphQL IDE',
    'description':'GraphiQL Explorer/Playground Enabled',
    'impact':'Information Leakage - /' + url.rsplit('/', 1)[-1],
    'severity':'LOW',
    'color': 'blue',
    'curl_verify':'',
    'error':None
  }

  heuristics = ('graphiql.min.css', 'GraphQL Playground', 'GraphiQL', 'graphql-playground')

  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  request_headers['Accept'] = 'text/html'
  response = request(url, proxies=proxy, headers=request_headers)
  process_response(res, response, expect_json=False)
  try:
    if response and hasattr(response, 'text') and any(word in response.text for word in heuristics):
      res['result'] = True
  except Exception:
      pass

  return res
