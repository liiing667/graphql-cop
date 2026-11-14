"""Field duplication tests."""
from lib.utils import build_headers, graph_query, process_response


def field_duplication(url, proxy, headers, debug_mode):
  """Check for field duplication."""
  res = {
    'result':False,
    'title':'Field Duplication',
    'description':'Queries are allowed with 500 of the same repeated field',
    'impact':'Denial of Service - /' + url.rsplit('/', 1)[-1],
    'severity':'HIGH',
    'color': 'red',
    'curl_verify':'',
    'error':None
  }

  duplicated_string = '__typename \n' * 500
  q = 'query cop { ' + duplicated_string + '} '
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  gql_response = graph_query(url, proxies=proxy, headers=request_headers, payload=q)
  body = process_response(res, gql_response)

  try:
    if body and body['data']['__typename']:
      res['result'] = True
  except Exception:
    pass

  return res
