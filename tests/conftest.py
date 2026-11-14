"""Pytest fixtures shared by the graphql-cop acceptance suite."""
import socket
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
  sys.path.insert(0, ROOT)

from tests.fake_graphql_server import FakeGraphQLServer  # noqa: E402


@pytest.fixture
def graphql_server():
  """Start an isolated fake GraphQL server for one test."""
  with FakeGraphQLServer() as server:
    yield server


@pytest.fixture
def make_server():
  """Factory for fake servers with custom response configuration."""
  created = []

  def _factory(**config):
    server = FakeGraphQLServer(**config)
    server.__enter__()
    created.append(server)
    return server

  yield _factory

  for server in created:
    server.__exit__(None, None, None)


@pytest.fixture
def closed_server_url():
  """Return a local URL whose port is closed (immediate connection refused)."""
  sock = socket.socket()
  sock.bind(('127.0.0.1', 0))
  host, port = sock.getsockname()
  sock.close()
  return 'http://{0}:{1}/graphql'.format(host, port)
