"""Checks mutation support over on GET."""
from lib.utils import build_headers, process_response, request


def get_based_mutation(url, proxies, headers, debug_mode):
  res = {
    'result':False,
    'title':'Mutation is allowed over GET (possible CSRF)',
    'description':'GraphQL mutations allowed using the GET method',
    'impact':'Possible Cross Site Request Forgery - /' + url.rsplit('/', 1)[-1],
    'severity':'MEDIUM',
    'color': 'yellow',
    'curl_verify':'',
    'error':None
  }

  q = 'mutation cop {__typename}'
  request_headers = build_headers(headers, res['title'] if debug_mode else None)
  response = request(url, proxies=proxies, headers=request_headers, params={'query':q})
  body = process_response(res, response)
  try:
    if body and body['data']['__typename']:
        res['result'] = True
  except Exception:
      pass

  return res
