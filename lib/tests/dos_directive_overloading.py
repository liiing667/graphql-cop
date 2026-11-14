"""Directive overloading tests."""
from lib.utils import build_headers, graph_query, process_response


def directive_overloading(url, proxy, headers, debug_mode):
  """Check for directive overloading."""
  res = {
    'result':False,
    'title':'Directive Overloading',
    'description':'Multiple duplicated directives allowed in a query',
    'impact':'Denial of Service - /' + url.rsplit('/', 1)[-1],
    'severity':'HIGH',
    'color': 'red',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop { __typename @aa@aa@aa@aa@aa@aa@aa@aa@aa@aa }'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload=q)
  body = process_response(res, gql_response)

  try:
    if body and len(body['errors']) == 10:
      res['result'] = True
  except Exception:
    pass

  return res
