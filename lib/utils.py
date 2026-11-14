"""Helper parts for graphql-cop."""
import os

import requests
from simplejson import JSONDecodeError
from version import VERSION

requests.packages.urllib3.disable_warnings()

# Stable error categories recorded in every test result under the "error" key
TRANSPORT_ERROR = 'transport'
HTTP_ERROR = 'http'
PROTOCOL_ERROR = 'protocol'
INTERNAL_ERROR = 'internal'

# Header values that must never be recorded verbatim in debugging evidence
REDACTED_HEADERS = (
    'authorization',
    'proxy-authorization',
    'cookie',
    'set-cookie',
)
REDACTED_VALUE = '[REDACTED]'


class RequestError(Exception):
  """A failed HTTP exchange with a stable, JSON-serializable shape."""

  def __init__(self, error_type, message):
    super().__init__(message)
    self.error_type = error_type
    self.message = message

  def as_dict(self):
    """Return a plain dictionary suitable for JSON output."""
    return {'type': self.error_type, 'message': self.message}


def build_headers(headers, debug_header=None):
  """Build an isolated header dictionary for a single request.

  The caller-provided headers are copied so that per-test mutations (the
  debug header, an Accept override, ...) never leak into other endpoints or
  tests.
  """
  request_headers = dict(headers or {})
  if debug_header:
    request_headers['X-GraphQL-Cop-Test'] = debug_header
  return request_headers


def redact_headers(headers):
  """Return a copy of the headers with sensitive values masked."""
  safe_headers = {}
  for key, value in (headers or {}).items():
    if key.lower() in REDACTED_HEADERS:
      safe_headers[key] = REDACTED_VALUE
    else:
      safe_headers[key] = value
  return safe_headers


def curlify(obj):
  """Render a response as a curl command, redacting sensitive headers."""
  if isinstance(obj, RequestError) or not hasattr(obj, 'request'):
    return ''
  req = obj.request
  command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
  method = req.method
  uri = req.url
  if req.body:
    try:
      data = req.body.decode('UTF-8')
    except Exception:
      reqb = bytes(req.body, 'UTF-8')
      data = reqb.decode('UTF-8')
  else:
    data = ''
  safe_headers = redact_headers(req.headers)
  headers = ['"{0}: {1}"'.format(k, v) for k, v in safe_headers.items()]
  headers = " -H ".join(headers)
  return command.format(method=method, headers=headers, data=data, uri=uri)


def get_error(resp):
  """Collect the error."""
  error = None
  try:
      error = resp['errors'][0]['message']
  except Exception:
      pass
  return error


def graph_query(url, proxies, headers, operation='query', payload={}, batch=False):
  """Perform a query."""
  if batch:
    data = []
    for _ in range(10):
      data.append({operation:payload})
  else:
    data = {operation:payload, "operationName":"cop"}
  try:
    response = requests.post(url,
                            headers=headers,
                            cookies=None,
                            verify=False,
                            allow_redirects=True,
                            timeout=60,
                            proxies=proxies,
                            json=data)
    return response
  except Exception as exc:
    return RequestError(TRANSPORT_ERROR, str(exc))


def request(url, proxies, headers, params=None, data=None, verb='GET'):
  """Perform requests."""
  try:
    response = requests.request(verb,
                            url=url,
                            params=params,
                            headers=headers,
                            cookies=None,
                            verify=False,
                            allow_redirects=True,
                            proxies=proxies,
                            timeout=20,
                            data=data)
    return response
  except Exception as exc:
    return RequestError(TRANSPORT_ERROR, str(exc))


def process_response(res, response, expect_json=True):
  """Record curl evidence and classify transport/HTTP/protocol errors.

  Populates ``res['curl_verify']`` and ``res['error']``. Returns the parsed
  JSON body for GraphQL responses, or ``None`` when the body cannot be used
  (the caller must stop processing in that case).
  """
  if isinstance(response, RequestError):
    res['curl_verify'] = ''
    res['error'] = response.as_dict()
    return None
  if response is None:
    res['curl_verify'] = ''
    res['error'] = {'type': TRANSPORT_ERROR, 'message': 'No response received'}
    return None

  res['curl_verify'] = curlify(response)

  if response.status_code >= 400:
    res['error'] = {
      'type': HTTP_ERROR,
      'message': 'HTTP {0} {1}'.format(response.status_code, response.reason),
    }

  if not expect_json:
    return None

  try:
    return response.json()
  except (JSONDecodeError, ValueError):
    if res['error'] is None:
      res['error'] = {
        'type': PROTOCOL_ERROR,
        'message': 'Response body is not valid GraphQL JSON',
      }
    return None


def is_graphql(url, proxies, headers, debug_mode):
  """Check if the URL provides a GraphQL interface."""
  request_headers = build_headers(
    headers, 'Looking for GraphQL Interface' if debug_mode else None)
  query = '''
    query cop {
      __typename
    }
  '''
  response = graph_query(url, proxies, request_headers, payload=query)

  if isinstance(response, RequestError) or response is None:
    return False

  try:
    body = response.json()
  except (JSONDecodeError, ValueError):
    return False
  if not isinstance(body, dict):
    return False

  data = body.get('data')
  if data is not None:
    if data.get('__typename') in ('Query', 'QueryRoot', 'query_root', 'Root'):
      return True
  errors = body.get('errors')
  if errors and (any('locations' in item for item in errors)
                 or any('extensions' in item for item in errors)):
    return True
  if data:
    return True
  return False

def draw_art():
  """Create banner."""
  return '''
                GraphQL Cop {version}
           Security Auditor for GraphQL
             Dolev Farhi & Nick Aleks
  '''.format(version=VERSION)


def read_custom_wordlist(location):
  wordlists = set()
  if os.path.exists(location):
    f = open(location, 'r').read()
    for line in f.splitlines():
      if not line.startswith('/'):
        line = '/' + line

      wordlists.add(line)
  else:
    print('Could not find wordlist file: {}'.format(location))
  return wordlists
