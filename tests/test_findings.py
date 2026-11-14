"""End-to-end findings against the fake GraphQL service."""
import json
from json import loads

from lib.tests import tests
from lib.tests.info_field_suggestions import field_suggestions
from lib.tests.info_graphiql import detect_graphiql
from lib.tests.info_trace_mode import trace_mode
from lib.tests.info_unhandled_error import unhandled_error_detection


def test_introspection_findings_stable(graphql_server):
  result = tests['introspection'](graphql_server.url, {}, {}, False)
  assert result['result'] is True
  assert result['error'] is None
  assert result['severity'] == 'HIGH'


def test_field_suggestions_detection(make_server):
  server = make_server()
  result = field_suggestions(server.url, {}, {}, False)
  assert result['result'] is True
  assert result['error'] is None


def test_graphiql_detection(make_server):
  server = make_server(graphiql=True)
  result = detect_graphiql(server.url, {}, {}, False)
  assert result['result'] is True
  assert result['error'] is None


def test_trace_mode_detection(make_server):
  server = make_server(tracing=True)
  result = trace_mode(server.url, {}, {}, False)
  assert result['result'] is True
  assert result['error'] is None


def test_unhandled_error_detection(make_server):
  server = make_server(unhandled=True)
  result = unhandled_error_detection(server.url, {}, {}, False)
  assert result['result'] is True
  assert result['error'] is None


def test_main_emits_complete_json(make_server, capsys):
  server = make_server()
  exit_code = __import__('graphql-cop', fromlist=['main']).main([
    '-t', server.url,
    '-o', 'json',
    '-d',
    '-H', '{"Authorization": "Bearer secret"}',
  ])

  assert exit_code == 0
  output = loads(capsys.readouterr().out)
  assert isinstance(output, list)
  assert len(output) == len(tests)
  for item in output:
    assert item['error'] is None
    assert 'secret' not in json.dumps(item)
    assert 'curl_verify' in item


def test_main_forced_scan_survives_unreachable_endpoint(closed_server_url, capsys):
  main = __import__('graphql-cop', fromlist=['main']).main
  exit_code = main([
    '-t', closed_server_url,
    '-o', 'json',
    '-f',
  ])

  assert exit_code == 0
  captured = capsys.readouterr().out
  output = loads(captured[captured.index('['):])
  assert len(output) == len(tests)
  assert all(item['error']['type'] == 'transport' for item in output)
