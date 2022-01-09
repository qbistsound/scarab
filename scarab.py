import sys
import csv
import getopt
import os.path
import concurrent.futures
import socket
import socks
import requests
import importlib

from lxml import html, etree

#global variables
BUFFER = []
ELEMENTS = []
ELEMENT_MAP = {"host": 1, "port": 2, "user": -1, "pass": -1}
CONFIG = { "method": "fs", "source": "", "parser": "text", "UA": "", "threads": 32, "host": "www.baidu.com", "echo": True, "method": "SOCKS5", "file": "list.txt"}
HELP = f"Usage: {sys.argv[0]} [-f file | -u url] [-p <text|table|csv|script:name>] [-o <output-file>] [-a <remote-addres>] [-t <thread-size>] [-m (index(host), index(port), index(user), index(password)]..."
#cpx(address, method) - calls the connection to proxy returns True or False
def cpx(address, method):
	socket_type = socks.SOCKS5
	if method == "HTTP": socket_type = socks.HTTP
	if method == "SOCKS4": socket_type = socks.SOCKS4
	so = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		user = getuser(address)
		auth = getpass(address)
		addr = socket.gethostbyname(getaddr(address, method))
		port = getport(address, method)
		if addr == "0.0.0.0": return False
		socket.inet_aton(addr) #validates the ip
		so.set_proxy(socket_type, addr, port, False, user, auth)
		so.settimeout(10)
		request = "GET / HTTP/1.0\r\nHost: " + CONFIG["host"] + "\r\n\r\n"
		so.connect((CONFIG["host"], 80))
		so.send(str.encode(request))
		response = so.recv(4096)
		so.close()
		return True if response.startswith(b"HTTP/1") else False
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
	if ":" not in elements[0]: return ""
	else: return elements[0].split(":")[1]
#gets user from address string
def getuser(address):
	if "@" not in address: return ""
	elements = address.split("@")
	if ":" not in elements[0]: return elements[0]
	else: return elements[0].split(":")[0]
	return ""
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
	if not os.path.exists(file_n): raise SystemExit(f"file not found: {file_n}")
	return open(file_n,'r').read()
#parses csv
def parse_csv(string):
	elements = []
	reader = csv.reader(string.split('\n'), delimiter=',')
	for row in reader:
		host = row[ELEMENT_MAP["host"]].strip()
		port = row[ELEMENT_MAP["port"]].strip()
		user = "" if ELEMENT_MAP["user"] < 0 else row[ELEMENT_MAP["user"]].strip()
		auth = "" if ELEMENT_MAP["pass"] < 0 else row[ELEMENT_MAP["pass"]].strip()
		host_t = host if port == "" else f"{host}:{port}"
		user_t = "" if user == "" else f"{user}:{auth}@"
		elements.append(f"{user_t}{host_t}")
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
	host = element[ELEMENT_MAP["host"]].text.strip()
	port = element[ELEMENT_MAP["port"]].text.strip()
	user = "" if ELEMENT_MAP["user"] < 0 else row[ELEMENT_MAP["user"]].text.strip()
	auth = "" if ELEMENT_MAP["pass"] < 0 else row[ELEMENT_MAP["pass"]].text.strip()
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
	ARGUMENTS, OPTIONS = getopt.getopt(sys.argv[1:],"hf:u:p:o:a:t:m:", ["help", "file=", "url=", "parser=", "output=", "address=", "threads=", "map="])
	for ARG, OPT in ARGUMENTS:
		if ARG in ("-h", "--help"): raise SystemExit(HELP)
		if ARG in ("-a", "--address"): CONFIG["host"] = OPT
		if ARG in ("-p", "--parser"): CONFIG["parser"] = OPT
		if ARG in ("-o", "--output"): CONFIG["file"] = OPT
		if ARG in ("-f", "--file"): CONFIG["method"] = "fs"; CONFIG["source"] = OPT
		if ARG in ("-u", "--url"): CONFIG["method"] = "url"; CONFIG["source"] = OPT
		if ARG in ("-m", "--map"): parse_map(OPT)
except getopt.GetoptError: raise SystemExit(HELP)
#read contents
CONTENT = text_f(CONFIG["source"]) if CONFIG["method"] == "fs" else text_u(CONFIG["source"])
#parse
if CONFIG["parser"] == "text": 	ELEMENTS = CONTENT.split("\n")
if CONFIG["parser"] == "table": ELEMENTS = parse_table(CONTENT)
if CONFIG["parser"] == "csv": ELEMENTS = parse_csv(CONTENT)
if CONFIG["parser"].startswith("script"): ELEMENTS = parse_ext(CONTENT)
#threads
with concurrent.futures.ThreadPoolExecutor(max_workers = int(CONFIG["threads"])) as executor:
	future_to_url = {executor.submit(cpx, url, CONFIG["method"]): url for url in ELEMENTS}
	for future in concurrent.futures.as_completed(future_to_url):
		url = future_to_url[future]
		if future.result() == True:
			BUFFER.append(url)
			if CONFIG["echo"] == True:
				print(f"{url}\t[OK]")
#output
print(BUFFER)
text_file = open(CONFIG["file"], "w")
text_file.write("\n".join(BUFFER))
text_file.close()
