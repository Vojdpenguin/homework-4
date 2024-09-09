from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, mimetypes, pathlib, socket, json, datetime, threading

UDP_IP = '127.0.0.1'
UDP_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        data_dict = {}
        key_value = data_parse.split('&')
        data_dict[date] = {}
        for el in key_value:
            if '=' in el:
                key, value = el.split('=', 1)
                data_dict[date][key] = value
        print(data_dict)
        self.send_to_udp(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    @staticmethod
    def send_to_udp(data_dict):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        message = json.dumps(data_dict).encode('utf-8')
        sock.sendto(message, (UDP_IP, UDP_PORT))
        print(f'Sending message: {data_dict} to {UDP_IP}:{UDP_PORT}')

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as fd:
            self.wfile.write(fd.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def run():
    server_address = ('', 3000)
    http = HTTPServer(server_address, HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((UDP_IP, UDP_PORT))
        print(f'Starting UDP server on {UDP_IP}:{UDP_PORT}')
        while True:
            data, addr = s.recvfrom(1024)
            print(f'Received message: {data.decode()} from {addr}')
            try:
                with open('storage/data.json', 'r') as fd:
                    data_dictionary = json.load(fd)
                    print(f'Data from file: {data_dictionary}')
            except json.JSONDecodeError:
                data_dictionary = {}
                print("Empty or invalid JSON. Initialized with an empty dictionary.")
            data_dictionary.update(json.loads(data.decode()))
            with open('storage/data.json', 'w') as fd:
                print(data_dictionary)
                json.dump(data_dictionary, fd, indent=4)
                print("Data saved to storage/data.json")


if __name__ == '__main__':
    udp_thread = threading.Thread(target=run_udp_server)
    serv_thread = threading.Thread(target=run)
    udp_thread.start()
    serv_thread.start()
