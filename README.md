# scarab
THE 30 MINUTE PROXY SCRAPER


Usage:

python3 scarab.py [-f file | -u url] [-p text|table|csv|script:name] [-o output-file] [-a remote-addres] [-t thread-size] [-c SOCKS5|SOCKS4|HTTP|HTTPS ] [-m (index(host), index(port), index(user), index(password)]
  
  -f <file> | --file=(file)       Defines file source to read from
  
  -u <url>  | --url=(url)         Defines a URL to read from instead
  
  -p <parser> | --parser=(parser) Defines a parser, parser types are explained below
  
  -o <file> | --output=(file)     Defines the output file, if left blank all data will be written to `list.txt` in the executing directory
  
  -a <host> | --address=(host)    Defines the remote address to check with the proxy, by default this is set to `google.com`
  
  -t <size> | --threads=(size)    Integer value, declares number of threads to run
  
  -m <map>  | --map=(map)         Defines field mapping for table and csv parsers, map options are described below.
  
  -s | --ssl                      Enables SSL connections, otherwise all proxy connections are attempted through TCP
  
  -c | --connection               Defines connection mode, accepted modes are SOCKS5, SOCKS4, HTTP, HTTPS
  
  -v | -verbose                   Enables Verbose mode.

  -x | -x-server=(port)           Starts simple HTTPD proxy service, this can be used without the -f command as long as the `--output=(file)` is declared or a list.txt exists in the executing folder.
  
  
  
# Parsers
  
  text: default text format, uses [user:password@]host:port format, where [user:password@] is optional.
  
  table: HTML table, script will traverse the table (including /table/tbody/tr and /table/tr), and extract values defined in mapping option
  
  csv:   CSV parsers, values are defined in mapping option
  
  script: Plugin script for processing content points to python script containing the parsing funciton, plugins are defined under plugin section.
  
  
# Mapping
  
  Scarab can map both CSV and TABLE parsers according to the position of values, the indexes are keyed as `["host", "port", "user", "password"]`, this will allow you to map fields as `-m 1,2` for Cell 1 which should contain the Host and Cell 2 which should contain the Port of the proxy server.  All mapping indexes start at 1, not 0.  This mapping is provided as an object to external plugin functions.  By default this value is set to `{"host": 1, "port": 2, "user": -1, "pass": -1}`, where -1 is ignored.
  
  ![image](https://user-images.githubusercontent.com/97387095/148680008-dc7f2b9f-cec6-47ff-be4d-7867d984d389.png)
  
  would translate to `python3 scarab.py -u http://myproxy.list -parser table -m 1,2`
  
  ![image](https://user-images.githubusercontent.com/97387095/148681117-c28ef3b2-681b-44a4-a9b1-f37947902284.png)

  would translate to `python3 scarab.py -f file.csv -parser csv -m 1,8`
  
# Plugins
  
  Scarab can also call external functions within the same directory it resides in to parse an element.  An example plugin is included, this file MUST include a _parse(string, map), where `string` represents the content from the file or url source, and `map` represents the mapping created by scarab before calling.  To use the plugin parser use `-p script:plugin` for plugin.py.
  
  ```
    def _parse(string, definition):
      elements = []
      ... your code ...
      return elements
  ```

# Server
  
  *scarab* now comes with a very simple built in http service, which can utilize the list.txt in executing folder or an external proxy list in [user:pass@]host:port format. ie. `python3 scarab.py -x 6666 -o proxy_list.txt` will launch a www server only using the provided file as the proxy list, no `-o` option is provided, the script will automatically look for a list.txt in the executing folder, while `python3 scarab.py -f file.csv -p csv -m 1,2 -x 6666` will process file.csv then launch a proxy server utilizing the proxies from the output file or list.txt in the executing folder.
  
# Details
  
  Written in 30 minutes between projects to prove that all of this can be done without extensive dependencies and massive amounts of calls and class objects, and provide a wider set of features, with an increased adaptibility.
