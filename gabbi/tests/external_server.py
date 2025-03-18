
import sys
from wsgiref import simple_server

from gabbi.tests import simple_wsgi

def run(port):
    server = simple_server.make_server("127.0.0.1", int(port), simple_wsgi.SimpleWsgi())
    server.serve_forever()

if __name__ == "__main__":
    port = sys.argv[1]
    run(port)
