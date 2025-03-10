import configparser
import logging
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId, json_util

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
collection_data = db[config.get('MongoDB', 'collection_data')]
collection_view = db[config.get('MongoDB', 'collection_view')]



class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data.decode('utf-8'))
            logger.info(f'Received data: {json_data}')
            
            result = collection_data.insert_one(json_data)
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
    
    def do_GET(self):
        request_path = self.path
        logger.debug(f"request_path: {request_path}")
        if '://' not in request_path:
            request_path = 'http://' + request_path
        parsed_path = urlparse(request_path)
        logger.debug(f"parsed_path: {parsed_path}")
        if parsed_path.path == '/latest':
            try:
                latest_doc = collection_view.find_one(sort=[('_id', -1)])
                
                if latest_doc:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    # Convert ObjectId to string for JSON serialization
                    latest_doc['_id'] = str(latest_doc['_id'])
                    self.wfile.write(json.dumps(latest_doc).encode('utf-8'))
                else:
                    self.send_error(404, 'No documents found')
            except Exception as e:
                logger.error(f"Error retrieving latest document: {str(e)}")
                self.send_error(500, str(e))
        elif parsed_path.path == '/data':
            try:
                cursor = collection_view.find().sort('_id', -1)#.limit(100)
                data = list(cursor)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                # Use json_util to handle ObjectId serialization
                self.wfile.write(json_util.dumps(data).encode('utf-8'))
            except Exception as e:
                logger.error(f"Error retrieving data: {str(e)}")
                self.send_error(500, str(e))
        else:
            self.send_error(404, 'Not Found')


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
