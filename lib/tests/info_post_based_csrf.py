"""Checks if queries are allowed over POST not in JSON."""
from lib.utils import build_headers, process_response, request


def post_based_csrf(url, proxies, headers, debug_mode):
  res = {
    'result':False,
    'title':'POST based url-encoded query (possible CSRF)',
    'description':'GraphQL accepts non-JSON queries over POST',
    'impact':'Possible Cross Site Request Forgery - /' + url.rsplit('/', 1)[-1],
    'severity':'MEDIUM',
    'color': 'yellow',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop { __typename }'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  response = request(url, proxies=proxies, headers=request_headers, data={'query': q}, verb='POST')
  body = process_response(res, response)
  try:
    if body and body['data']['__typename']:
        res['result'] = True
  except Exception:
      pass

  return res
