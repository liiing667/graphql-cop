"""Stable recording of transport, HTTP and protocol errors."""
from lib.tests.info_introspect import introspection
from lib.utils import HTTP_ERROR, PROTOCOL_ERROR, TRANSPORT_ERROR


REQUIRED_KEYS = {
  'result', 'title', 'description', 'impact',
  'severity', 'color', 'curl_verify', 'error',
}


def test_transport_error_is_recorded(closed_server_url):
  result = introspection(closed_server_url, {}, {'Authorization': 'Bearer x'}, False)

  assert REQUIRED_KEYS.issubset(result.keys())
  assert result['result'] is False
  assert result['error']['type'] == TRANSPORT_ERROR
  assert result['error']['message']
  assert result['curl_verify'] == ''


def test_http_error_is_recorded(make_server):
  server = make_server(fail_http=True)

  result = introspection(server.url, {}, {}, False)

  assert result['error']['type'] == HTTP_ERROR
  assert '500' in result['error']['message']
  assert result['curl_verify']


def test_protocol_error_is_recorded(make_server):
  server = make_server(invalid_json=True)

  result = introspection(server.url, {}, {}, False)

  assert result['error']['type'] == PROTOCOL_ERROR
  assert result['error']['message']
  assert result['curl_verify']
