"""A small in-process fake GraphQL server used by the pytest suite.

Only Python standard-library modules are used so the acceptance tests do not
need any external service. Every received request is recorded so tests can
assert how headers are carried between calls.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class FakeGraphQLHandler(BaseHTTPRequestHandler):
  """Serves canned GraphQL responses for graphql-cop's tests."""

  def log_message(self, *args):
    pass

  @property
  def config(self):
    return self.server.config

  def _record(self, method, headers, body):
    self.server.requests.append({
      'method': method,
      'path': urlparse(self.path).path,
      'headers': dict(headers),
      'body': body,
    })

  def _send(self, payload, status=200, content_type='application/json'):
    if isinstance(payload, (dict, list)):
      raw = json.dumps(payload).encode('utf-8')
    else:
      raw = payload.encode('utf-8')
    self.send_response(status)
    self.send_header('Content-Type', content_type)
    self.send_header('Content-Length', str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)

  def _graphql_payload(self, query, batch):
    """Produce a plausible GraphQL body for the canned queries."""
    if batch:
      return [{'data': {'__typename': 'Query'}} for _ in batch]

    if '__schema' in query and 'directive' in query:
      return {
        'errors': [
          {'message': 'Cannot query field "directive" on "__Schema". Did you mean "directives"?'}
        ]
      }
    if '__schema' in query:
      types = [{'name': 'Type{}'.format(i), 'fields': []} for i in range(30)]
      return {'data': {'__schema': {'types': types}}}
    if query.strip().startswith('mutation'):
      if self.config.get('disable_get'):
        return {'errors': [{'message': 'mutations over GET are not allowed'}]}
      return {'data': {'__typename': 'Query'}}
    if self.config.get('tracing'):
      return {
        'errors': [
          {'extensions': {'tracing': {'version': 1, 'duration': 0}}}
        ]
      }
    if self.config.get('unhandled'):
      return {
        'errors': [
          {'extensions': {'exception': {'stacktrace': ['line 1']}}}
        ]
      }
    if query.startswith('qwerty'):
      return {'errors': [{'message': 'syntax error'}]}
    if '@aa' in query:
      return {'errors': [{'message': 'duplicate directive'} for _ in range(10)]}
    return {'data': {'__typename': 'Query'}}

  def do_GET(self):
    parsed = urlparse(self.path)
    params = parse_qs(parsed.query)
    self._record('GET', self.headers, params)
    if self.config.get('graphiql') and 'query' not in params:
      return self._send('<html><body>GraphiQL GraphQL Playground</body></html>',
                        content_type='text/html')
    if 'query' not in params:
      return self._send({'errors': [{'message': 'missing query'}]})
    if self.config.get('disable_get'):
      return self._send({'errors': [{'message': 'GET is not supported'}]})
    return self._send(self._graphql_payload(params['query'][0], False))

  def do_POST(self):
    length = int(self.headers.get('Content-Length', 0))
    raw = self.rfile.read(length) if length else b''
    self._record('POST', self.headers, raw)

    if self.config.get('fail_http'):
      return self._send({'errors': [{'message': 'boom'}]}, status=500)
    if self.config.get('invalid_json'):
      return self._send('this is not json', content_type='text/plain')

    content_type = self.headers.get('Content-Type', '')
    if 'application/json' not in content_type:
      try:
        form = parse_qs(raw.decode('utf-8'))
        query = form['query'][0]
      except Exception:
        return self._send({'errors': [{'message': 'bad form body'}]})
      if self.config.get('disable_form_post'):
        return self._send({'errors': [{'message': 'form posts rejected'}]})
      return self._send(self._graphql_payload(query, False))

    try:
      body = json.loads(raw.decode('utf-8'))
    except Exception:
      return self._send({'errors': [{'message': 'bad json'}]})

    if isinstance(body, list):
      return self._send(self._graphql_payload('', body))
    query = body.get('query', '')
    return self._send(self._graphql_payload(query, False))


class FakeGraphQLServer:
  """Context manager wrapping a threaded fake server on an ephemeral port."""

  def __init__(self, **config):
    self.config = config
    self.requests = []
    self._httpd = None
    self._thread = None

  def __enter__(self):
    self._httpd = ThreadingHTTPServer(('127.0.0.1', 0), FakeGraphQLHandler)
    self._httpd.config = self.config
    self._httpd.requests = self.requests
    self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
    self._thread.start()
    return self

  def __exit__(self, *exc):
    self._httpd.shutdown()
    self._httpd.server_close()
    self._thread.join(timeout=5)

  @property
  def url(self):
    host, port = self._httpd.server_address
    return 'http://{0}:{1}/graphql'.format(host, port)
