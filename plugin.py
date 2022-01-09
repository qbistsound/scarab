import base64

from lxml import html, etree
# reads [http://free-proxy.cz/en/proxylist/country/all/socks5/ping/all]
def _parse(string, definition):
	elements = []
	xmldoc = html.fromstring(string)
	for element in xmldoc.findall('.//table/tbody/tr'):
		host_cell = element[0].xpath("./script")
		if not host_cell[0].text is None:
			host = base64.b64decode(host_cell[0].text.replace("document.write(Base64.decode(\"", "").replace("\"))", "")).decode("utf-8")
			port = element[1].xpath("./span")[0].text
			elements.append(f"{host}:{port}")
	return elements
