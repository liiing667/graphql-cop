"""Debugging evidence must not leak caller secrets."""
from lib.tests.info_introspect import introspection
from lib.utils import RequestError, curlify, redact_headers


def test_curl_verify_redacts_authorization(graphql_server):
  result = introspection(
    graphql_server.url, {},
    {'Authorization': 'Bearer super-secret-token'}, True,
  )

  assert result['error'] is None
  assert 'Bearer super-secret-token' not in result['curl_verify']
  assert '[REDACTED]' in result['curl_verify']
  assert 'X-GraphQL-Cop-Test' in result['curl_verify']


def test_redact_headers_masks_sensitive_values():
  safe = redact_headers({
    'Authorization': 'Bearer token',
    'Proxy-Authorization': 'Basic abc',
    'Cookie': 'session=1',
    'User-Agent': 'graphql-cop',
  })

  assert safe['Authorization'] == '[REDACTED]'
  assert safe['Proxy-Authorization'] == '[REDACTED]'
  assert safe['Cookie'] == '[REDACTED]'
  assert safe['User-Agent'] == 'graphql-cop'


def test_curlify_is_safe_without_response():
  assert curlify(RequestError('transport', 'boom')) == ''
  assert curlify(None) == ''
