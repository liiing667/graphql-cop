"""Acceptance tests for per-endpoint/test header isolation."""
import copy

from lib.tests import tests
from lib.tests.info_graphiql import detect_graphiql
from lib.tests.info_introspect import introspection
from lib.utils import is_graphql


def test_each_test_gets_isolated_headers(graphql_server):
  base_headers = {'Authorization': 'Bearer caller-token'}
  original = copy.deepcopy(base_headers)

  for test_name, test in tests.items():
    result = test(graphql_server.url, {}, dict(base_headers), True)
    assert 'error' in result
    assert result['error'] is None

  assert base_headers == original
  assert 'X-GraphQL-Cop-Test' not in base_headers

  debug_names = [
    request['headers'].get('X-GraphQL-Cop-Test')
    for request in graphql_server.requests
  ]
  assert debug_names
  assert all(name for name in debug_names)
  assert len(set(debug_names)) > 1


def test_debug_header_does_not_leak_between_tests(graphql_server):
  headers = {'Authorization': 'Bearer caller-token'}

  introspection(graphql_server.url, {}, dict(headers), True)
  detect_graphiql(graphql_server.url, {}, dict(headers), False)

  debug_requests = [
    request for request in graphql_server.requests
    if 'X-GraphQL-Cop-Test' in request['headers']
  ]
  no_debug_requests = [
    request for request in graphql_server.requests
    if 'X-GraphQL-Cop-Test' not in request['headers']
  ]
  assert debug_requests and no_debug_requests
  assert all(
    request['headers']['Authorization'] == 'Bearer caller-token'
    for request in graphql_server.requests
  )


def test_accept_override_is_scoped_to_graphiql_test(graphql_server):
  headers = {'Accept': 'application/json'}

  detect_graphiql(graphql_server.url, {}, dict(headers), True)
  introspection(graphql_server.url, {}, dict(headers), True)

  graphiql_request = next(
    request for request in graphql_server.requests
    if request['headers'].get('X-GraphQL-Cop-Test') == 'GraphQL IDE'
  )
  introspection_request = next(
    request for request in graphql_server.requests
    if request['headers'].get('X-GraphQL-Cop-Test') == 'Introspection'
  )
  assert graphiql_request['headers']['Accept'] == 'text/html'
  assert introspection_request['headers']['Accept'] == 'application/json'
  assert headers == {'Accept': 'application/json'}


def test_is_graphql_uses_isolated_headers(graphql_server):
  headers = {'Authorization': 'Bearer caller-token'}
  assert is_graphql(graphql_server.url, {}, dict(headers), True) is True
  assert headers == {'Authorization': 'Bearer caller-token'}
  assert 'X-GraphQL-Cop-Test' not in headers
