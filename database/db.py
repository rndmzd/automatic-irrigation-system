import configparser
import logging
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

config = configparser.ConfigParser()
config.read("config.ini")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

client = MongoClient(
    host=config.get('MongoDB', 'host'),
    port=config.getint('MongoDB', 'port'),
)
db = client[config.get('MongoDB', 'db')]
collection = db[config.get('MongoDB', 'collection')]


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data.decode('utf-8'))
            logger.info(f'Received data: {json_data}')
            
            result = collection.insert_one(json_data)
            logger.debug(f"result.inserted_id: {result.inserted_id}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'message': 'Data saved successfully', 'id': str(result.inserted_id)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON data')
        except Exception as e:
            self.send_error(500, str(e))


def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    logger.info(f'Server running on port {port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server is shutting down...")
    finally:
        httpd.server_close()
        client.close()
        logger.info("Server has shut down.")


if __name__ == '__main__':
    run_server()
