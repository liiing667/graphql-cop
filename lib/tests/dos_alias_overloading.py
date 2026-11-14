"""Alias overloading tests."""
from lib.utils import build_headers, graph_query, process_response


def alias_overloading(url, proxy, headers, debug_mode):
  """Check for alias overloading."""
  res = {
    'result':False,
    'title':'Alias Overloading',
    'description':'Alias Overloading with 100+ aliases is allowed',
    'impact':'Denial of Service - /' + url.rsplit('/', 1)[-1],
    'severity':'HIGH',
    'color': 'red',
    'curl_verify':'',
    'error':None
  }
  aliases = ''

  for i in range(0, 101):
     aliases += 'alias{}:__typename \n'.format(i)

  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload='query cop { ' + aliases + ' }')
  body = process_response(res, gql_response)

  try:
    if body and body['data']['alias100']:
      res['result'] = True
  except Exception:
    pass

  return res
