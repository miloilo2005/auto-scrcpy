from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import subprocess
import socket
import re


class CommandHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/execute':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(body.decode())

            command = params.get('command', [''])[0]
            print(f"Running command: {command}")

            try:
                if command.strip().lower().startswith("nmap"):
                    ip_match = re.search(r'ip:\s*([\d.]+)', command, re.IGNORECASE)
                    code_match = re.search(r'code:\s*(\d+)', command, re.IGNORECASE)
                    if ip_match and code_match:
                        ip = ip_match.group(1)
                        code = code_match.group(1)
                        command = f"nmap -sT {ip} -p 37000-44000"
                        print(f"Running command: {command}")
                        port_result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                        open_ports = re.findall(r'(\d+)/tcp\s+open', port_result.decode())
                        paired = False
                        success_responses = {
                                    b"Successfully paired with device.",
                                    b"Already paired with device.",
                                    b"Device is already paired.",
                                    b"Pairing was successful.",
                                    b"Pairing was successful. You can now connect to the device.",
                                    b"Pairing was successful. You can now connect to the device. Use 'adb connect' to connect to the device.",
                                    b"Pairing was successful. You can now connect to the device. Use 'adb connect <ip>:<port>' to connect to the device."
                            }
                        for port in open_ports:
                            command = f"adb pair {ip}:{port} {code}"
                            print(f"Trying: {command}")
                            try:
                                adbResult = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                                if adbResult.strip() in success_responses:
                                    print(f"Paired on port {port}")
                                    command = f"scrcpy"
                                    print(f"Running command: {command}")
                                    scrcpyResult = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                                    self.send_response(200)
                                    self.end_headers()
                                    self.wfile.write(scrcpyResult)
                                    paired = True
                                    break
                            except:
                                print(f"Failed to pair on port {port}")
                        else:
                            self.send_response(400)
                            self.end_headers()
                            self.wfile.write(b"ADB pairing unsuccessful.")
                            return
                        if not paired:
                            self.send_response(400)
                            self.end_headers()
                            self.wfile.write(b"No open port found.")
                            return
                    else: #double-check
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Invalid IP and code format for nmap.")
                        return
                #result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                #self.send_response(200)
                #self.end_headers()
                #self.wfile.write(result)
            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(e.output)

def run(server_class=HTTPServer, handler_class=CommandHandler):
    server_address = ('0.0.0.0', 8080)
    httpd = server_class(server_address, handler_class)
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server listening on {local_ip}:8080")
    print('Listening on port 8080...')
    httpd.serve_forever()

run()