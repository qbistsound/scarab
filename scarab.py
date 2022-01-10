import os.path
import random
import http.server
import importlib
import urllib.request
import socketserver
import concurrent.futures
import sys, csv, getopt
import socket, socks, ssl, requests
from lxml import html, etree
from contextlib import suppress
#global variables
HTTPD = None; BUFFER = []; ELEMENTS = []; PROXYSET = []; ELEMENT_MAP = {"host": 1, "port": 2, "user": -1, "pass": -1}
CONFIG = { "method": "fs", "source": "", "parser": "text", "UA": "", "threads": 128, "host": "google.com", "echo": False, "type": "SOCKS5", "file": "list.txt", "ssl": False, "timeout": 10, "xserver": -1}
HELP = f"Usage: {sys.argv[0]} [-f file | -u url] [-p <text|table|csv|script:name>] [-o <output-file>] [-a <remote-addres>] [-t <thread-size>] [-c SOCKS5|SOCKS4|HTTP|HTTPS] [-m (index(host), index(port), index(user), index(password)] [-v] [-x port]..."
#signal
def signal_handle(sig, frame): print("stopping server"); HTTPD.stop(); sys.exit(0);
#proxy server class
class scproxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
    	self.send_response(200)
    	self.end_headers()
    	request = None
    	with suppress(ValueError): request = urllib.request.Request(self.path[1:])
    	if request == None: return
    	parameters = select_list()
    	stype = "http" if CONFIG["ssl"] == False else "https"
    	if parameters == None: return
    	request.set_proxy(f"{parameters['host']}:{parameters['port']}", stype)
    	self.copyfile(urllib.request.urlopen(request, timeout=CONFIG["timeout"]), self.wfile)
#select proxy
def select_list():
	elements = text_f(CONFIG["file"]).split("\n")
	if len(elements) < 1: return None
	element = elements[random.randint(0, (len(elements) - 1))]
	return {"host": getaddr(element, "HTTP"), "port": getport(element, "HTTP"), "user": getuser(element), "pass": getpass(element) }
#start server
def start_xserver(port):
	parameters = select_list()
	HTTPD = socketserver.ForkingTCPServer(('', port), scproxy)
	print(f"proxy service started @ {port}")
	HTTPD.serve_forever()
#cpx(address, method) - calls the connection to proxy returns True or False
def cpx(address, method):
	socket_type = socks.SOCKS5
	if method == "HTTPS": socket_type = -1
	if method == "HTTP": socket_type = socks.HTTP
	if method == "SOCKS4": socket_type = socks.SOCKS4
	so = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		addr = socket.gethostbyname(getaddr(address, method))
		url = f"http://{CONFIG['host']}" if CONFIG["ssl"] == False else f"https://{CONFIG['host']}"
		if addr == "0.0.0.0": return False
		if socket_type == socks.HTTP: #HTTP
			pxd = { "http": f"http://{address}" }
			response = requests.get(url, timeout=CONFIG["timeout"], proxies=pxd)
			return False if not response.status_code == 200 else True
		if socket_type == -1: #HTTPS
			pxd = { "http": f"http://{address}", "https": f"https://{address}" }
			response = requests.get(url, timeout=CONFIG["timeout"], proxies=pxd)
			return False if not response.status_code == 200 else True
		#CONTINUE
		socket.inet_aton(addr) #validates the ip
		so.set_proxy(socket_type, addr, getport(address, method), False, getuser(address), getpass(address))
		so.settimeout(CONFIG["timeout"])
		cport = 443 if CONFIG["ssl"] == True else 80
		so.connect((CONFIG["host"], cport))
		#ssl wrap
		ssock = ssl.SSLContext(ssl.PROTOCOL_SSLv23).wrap_socket(so) if CONFIG["ssl"] == True else so
		#request
		ssock.send(str.encode("GET / HTTP/1.0\r\nHost: " + CONFIG["host"] + "\r\n\r\n"))
		response = ssock.recv(128)
		if not response.startswith(b"HTTP/1"): return False
		#ssl check
		if CONFIG["ssl"] == True:
			if len(ssl.DER_cert_to_PEM_cert(ssock.getpeercert(True))) <= 0: return False
		#close
		ssock.close()
		so.close()
		return True
	except socket.error as e:
		if CONFIG["echo"] == True: print(f"socket.error: {address} {e}")
		return False
	except socks.ProxyError as e:
		if CONFIG["echo"] == True: print(f"proxy.error: {address} {e}")
		return False
#gets password from address string
def getpass(address):
	if "@" not in address: return ""
	elements = address.split("@")
	return "" ""if ":" not in elements[0] else elements[0].split(":")[1]
#gets user from address string
def getuser(address):
	if "@" not in address: return ""
	elements = address.split("@")
	return elements[0] if ":" not in elements[0] else elements[0].split(":")[0]
#gets address from address string	
def getaddr(address, method): return address.split(":")[0] if "@" not in address else address.split("@")[1].split(":")[0]
#gets port from address string with defaults
def getport(address, method):
	elements = address.split(":") if "@" not in address else address.split("@")[1].split(":")
	if len(elements) >= 2:
		if elements[1].isnumeric(): return int(elements[1])
	if method == "SOCK5": return 1080
	if method == "SOCK4": return 1080
	return 8080
#read url
def text_u(url_n): return requests.get(url_n).text
#reads textfile into string
def text_f(file_n):
	if not os.path.exists(file_n):
		if CONFIG["xserver"] <= 0:
			raise SystemExit(f"file not found: {file_n}")
		else: return ""
	return open(file_n,'r').read()
#parses csv
def parse_csv(string):
	elements = []
	reader = csv.reader(string.split('\n'), delimiter=',')
	for row in reader:
		user = "" if ELEMENT_MAP["user"] < 0 else row[ELEMENT_MAP["user"]].strip()
		auth = "" if ELEMENT_MAP["pass"] < 0 else row[ELEMENT_MAP["pass"]].strip()
		elements.append(concat_addr(row[ELEMENT_MAP["host"]], row[ELEMENT_MAP["port"]], user, auth))
	return elements
#parses table
def parse_table(string):
	elements = []
	xmldoc = html.fromstring(string)
	for element in xmldoc.findall('.//table/tbody/tr'):
		if not element[ELEMENT_MAP["host"]].text is None: elements.append(parse_xmld(element))
	for element in xmldoc.findall('.//table/tr'):
		if not element[ELEMENT_MAP["host"]].text is None: elements.append(parse_xmld(element))
	return elements
#parse xmld
def parse_xmld(element):
	user = "" if ELEMENT_MAP["user"] < 0 else row[ELEMENT_MAP["user"]].text.strip()
	auth = "" if ELEMENT_MAP["pass"] < 0 else row[ELEMENT_MAP["pass"]].text.strip()
	return concat_addr(element[ELEMENT_MAP["host"]].text, element[ELEMENT_MAP["port"]].text, user, auth)
#concatr
def concat_addr(host, port, user, auth):
	host_t = host if port == "" else f"{host}:{port}"
	user_t = "" if user == "" else f"{user}:{auth}@"
	return f"{user_t}{host_t}"
#parse map
def parse_map(string):
	keys = list(ELEMENT_MAP.keys());
	elements = string.split(",")
	for index in range(len(keys)):
		if index < len(elements):
			if elements[index].isnumeric():
				ELEMENT_MAP[keys[index]] = int(elements[index]) - 1
#parse external
def parse_ext(string):
	script_arr = CONFIG["parser"].split(":")
	if not script_arr: return []
	if len(script_arr) <= 1: return []
	module = importlib.import_module(script_arr[1])
	return module._parse(string, ELEMENT_MAP)
#start
try:
	ARGUMENTS, OPTIONS = getopt.getopt(sys.argv[1:],"hf:u:p:o:c:a:t:m:x:vs", ["help", "file=", "url=", "parser=", "output=", "connection=", "address=", "threads=", "map=", "x-server=", "verbose", "ssl"])
	for ARG, OPT in ARGUMENTS:
		if ARG in ("-h", "--help"): raise SystemExit(HELP)
		if ARG in ("-a", "--address"): CONFIG["host"] = OPT
		if ARG in ("-p", "--parser"): CONFIG["parser"] = OPT
		if ARG in ("-o", "--output"): CONFIG["file"] = OPT
		if ARG in ("-c", "--connection"): CONFIG["type"] = OPT.upper()
		if ARG in ("-v", "--verbose"): CONFIG["echo"] = True
		if ARG in ("-s", "--ssl"): CONFIG["ssl"] = True
		if ARG in ("-f", "--file"): CONFIG["method"] = "fs"; CONFIG["source"] = OPT
		if ARG in ("-u", "--url"): CONFIG["method"] = "url"; CONFIG["source"] = OPT
		if ARG in ("-m", "--map"): parse_map(OPT)
		if ARG in ("-x", "--x-server"): CONFIG["xserver"] = int(OPT) if OPT.isnumeric() else -1
except getopt.GetoptError: raise SystemExit(HELP)
CONTENT = text_f(CONFIG["source"]) if CONFIG["method"] == "fs" else text_u(CONFIG["source"])
#parse
if CONFIG["parser"] == "text": 	ELEMENTS = CONTENT.split("\n")
if CONFIG["parser"] == "table": ELEMENTS = parse_table(CONTENT)
if CONFIG["parser"] == "csv": ELEMENTS = parse_csv(CONTENT)
if CONFIG["parser"].startswith("script"): ELEMENTS = parse_ext(CONTENT)
#threads
with concurrent.futures.ThreadPoolExecutor(max_workers = int(CONFIG["threads"])) as executor:
	future_set = {executor.submit(cpx, url, CONFIG["type"]): url for url in ELEMENTS}
	for future in concurrent.futures.as_completed(future_set):
		url = future_set[future]
		if future.result() == True:
			BUFFER.append(url)
			if CONFIG["echo"] == True:
				print(f"{url}\t[OK]")
#output
if len(BUFFER) > 0:
	text_file = open(CONFIG["file"], "wt")
	text_file.write("\n".join(BUFFER))
	text_file.close()
if CONFIG["xserver"] > 0:
	start_xserver(CONFIG["xserver"])
	signal.signal(signal.SIGINT, signal_handle)
