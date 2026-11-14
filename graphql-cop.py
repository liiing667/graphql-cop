#!/usr/bin/env python3
import sys

from json import loads, dumps
from optparse import OptionParser
from version import VERSION
from config import HEADERS
from urllib.parse import urlparse

from lib.tests import tests
from lib.utils import (
  INTERNAL_ERROR,
  build_headers,
  is_graphql,
  draw_art,
  read_custom_wordlist,
)

from termcolor import colored


def parse_options(argv=None):
  """Parse command line options."""
  parser = OptionParser(usage='%prog -t http://example.com -o json')
  parser.add_option('-t', '--target', dest='url', help='target url with the path - if a GraphQL path is not provided, GraphQL Cop will iterate through a series of common GraphQL paths')
  parser.add_option('-H', '--header', dest='header', action='append', help='Append Header(s) to the request \'{"Authorization": "Bearer eyjt"}\' - Use multiple -H for additional Headers')
  parser.add_option('-o', '--output', dest='format',
                          help='json', default=False)
  parser.add_option('-e', '--excluded-tests', dest='excluded_tests',
                          help='Exclude specific tests (comma separated)', default=[])
  parser.add_option('-l', '--list-tests', dest='list_tests', action='store_true',
                          help='List avaialble tests', default=False)
  parser.add_option('-f', '--force', dest='forced_scan', action='store_true',
                          help='Forces a scan when GraphQL cannot be detected', default=False)
  parser.add_option('-d', '--debug', dest='debug_mode', action='store_true',
                          help='Append a header with the test name for debugging', default=False)
  parser.add_option('-x', '--proxy', dest='proxy', default=None,
                    help='HTTP(S) proxy URL in the form http://user:pass@host:port')
  parser.add_option('-w', '--wordlist', dest='wordlist', default=False, help='Path to a list of custom GraphQL endpoints')
  parser.add_option('--version', '-v', dest='version', action='store_true', default=False,
                          help='Print out the current version and exit.')
  parser.add_option('--tor','-T', dest='tor', action='store_true', default=False,
                    help='Sends the request through the Tor network (ensure Tor is running and properly configured)')

  options, args = parser.parse_args(argv)
  return parser, options


def run_test(test, path, proxy, base_headers, debug_mode):
  """Run a single test against an endpoint with an isolated header copy."""
  try:
    return test(path, proxy, dict(base_headers), debug_mode)
  except Exception as exc:
    return {
      'result': False,
      'title': getattr(test, '__name__', 'unknown'),
      'description': 'Test failed to execute',
      'impact': 'Unknown - /' + path.rsplit('/', 1)[-1],
      'severity': 'INFO',
      'color': 'green',
      'curl_verify': '',
      'error': {'type': INTERNAL_ERROR, 'message': str(exc)},
    }


def main(argv=None):
  parser, options = parse_options(argv)

  proxy = {}

  if options.version:
    print('version:', VERSION)
    return 0

  if options.list_tests:
    print("\n".join(tests.keys()))
    return 0

  if not options.url:
    print(draw_art())
    parser.print_help()
    return 1

  if options.proxy:
    proxy = {
      'http': options.proxy,
      'https': options.proxy
    }

  selected_tests = dict(tests)
  if options.excluded_tests:
    for excluded_test in options.excluded_tests.split(','):
      try:
        del selected_tests[excluded_test]
      except KeyError:
        print(f'{excluded_test} cannot be excluded, skipping')

  elif options.tor:
    import socks
    import socket

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
    socket.socket = socks.socksocket

    proxy = {}

  # HEADERS only ever holds caller-provided headers. Per-request copies are
  # created inside is_graphql()/run_test(), so debug and Accept headers never
  # leak between endpoints or tests.
  if options.header is not None:
    for raw_header in options.header:
      try:
        HEADERS.update(loads(raw_header))
      except Exception:
        print("Cannot cast %s into header dictionary. Ensure the format \'{\"key\": \"value\"}\'." % raw_header)

  if not urlparse(options.url).scheme:
    print("URL missing scheme (http:// or https://). Ensure URL contains some scheme.")
    return 1

  if options.wordlist:
    endpoints = read_custom_wordlist(options.wordlist)
  else:
    endpoints = ['/', '/graphiql', '/playground', '/console', '/graphql']

  paths = []
  parsed = urlparse(options.url)

  if parsed.path and parsed.path != '/':
    paths.append(options.url)
  else:
    for endpoint in endpoints:
      paths.append(parsed.scheme + '://' + parsed.netloc + endpoint)

  json_output = []

  for path in paths:
    endpoint_headers = build_headers(HEADERS)
    if not is_graphql(path, proxy, endpoint_headers, options.debug_mode):
      if not options.forced_scan:
        print(path, 'does not seem to be running GraphQL. (Consider using -f to force the scan if GraphQL does exist on the endpoint)')
        continue
      else:
        print('Running a forced scan against the endpoint')
    for test in selected_tests.values():
      json_output.append(run_test(test, path, proxy, endpoint_headers, options.debug_mode))

  json_output = sorted(json_output, key=lambda item: item['title'])

  if options.format == 'json':
    print(dumps(json_output))
  else:
    for item in json_output:
      if item['result']:
        print('[{}] {} - {} ({})'.format(colored(item['severity'], item['color'], attrs=['bold']), colored(item['title'], 'white', attrs=['bold']), item['description'], item['impact']))

  return 0


if __name__ == '__main__':
  sys.exit(main())
