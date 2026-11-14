"""Collect all supported methods."""
from lib.utils import build_headers, process_response, request


def get_method_support(url, proxies, headers, debug_mode):
  """Get the supported methods."""
  res = {
    'result':False,
    'title':'GET Method Query Support',
    'description':'GraphQL queries allowed using the GET method',
    'impact':'Possible Cross Site Request Forgery (CSRF) - /' + url.rsplit('/', 1)[-1],
    'severity':'MEDIUM',
    'color': 'yellow',
    'curl_verify':'',
    'error':None
  }

  q = 'query cop {__typename}'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  response = request(url, proxies=proxies, headers=request_headers, params={'query':q})
  body = process_response(res, response)

  try:
    if body and body['data']['__typename']:
      res['result'] = True
  except Exception:
      pass

  return res
