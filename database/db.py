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
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/latest':
            try:
                # Retrieve the latest document
                latest_doc = collection.find_one(sort=[('_id', -1)])
                
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
                # Retrieve all documents, sorted by _id in descending order
                cursor = collection.find().sort('_id', -1).limit(100)  # Limit to last 100 entries
                data = list(cursor)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')  # Allow any origin
                self.end_headers()
                # Use json_util to handle ObjectId serialization
                self.wfile.write(json_util.dumps(data).encode('utf-8'))
            except Exception as e:
                logger.error(f"Error retrieving data: {str(e)}")
                self.send_error(500, str(e))
        elif parsed_path.path == '/config':
            try:
                config_data = {
                    'apiUrl': f'http://{self.server.server_address[0]}:{self.server.server_address[1]}'
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(config_data).encode('utf-8'))
            except Exception as e:
                logger.error(f"Error retrieving config: {str(e)}")
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
