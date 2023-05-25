import cv2
import logging
import socketserver
from threading import Condition
from threading import Thread
from http import server
from importlib import import_module
import os
import sys
import time

try:
	import webcam as camera
except:
	import utils.camera.webcam as camera

PAGE="""\

<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="X-UA-Compatible" content="ie=edge">
	<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.4.1/css/all.css" integrity="sha384-5sAR7xN1Nv6T6+dT2mhtzEpVJvfS3NScPQTrOxhwjIuvcA67KV2R5Jz6kr4abQsz" crossorigin="anonymous">
	<title>Odyssey Webcam</title>
	
	<style>
		/* global */
		@import url('https://fonts.googleapis.com/css?family=Roboto');

		.grid-2{
				display: grid;
				grid-template-columns: repeat(2,1fr);
		}

		body{
				margin: 0;
				padding: 0;
				font-family: 'Roboto', sans-serif;
				background-color: #101214;
				color: #7A7C80;

		}

		h2,.white{
				color: #fff;
		}

		a{
				color: #7A7C80;
				text-decoration: none;
		}
		/* section 1 */
		.section-1{
				padding-top: 40vh;
				text-align: center;
		}

		.section-1 p{
				font-size: 1.1rem;
				padding-bottom: 10px;
				margin:0;
		}

		.section-1 h2{
				font-size: 1.7rem;
				margin-bottom: 10px;
		}

		.section-1 a{
				font-size: 1.5rem;
				padding: 10px;
		}
		/* section 2 */
		.section-2{
				padding-top: 30vh;
				width: 70%;
		}

		.section-2 h2{
				font-size: 1.7rem;
				margin-bottom: 10px;
		}

		.section-2 p{
				font-size: 1.1rem;
				padding-bottom: 10px;
				margin:0;
		}

		.section-2 a{
				display: block;
				padding: 5px;
				font-size: 1.2rem;
				padding-left: 0;
				width: 100px;
		}
		/* animations / utilities */
		.section-2 a:hover{
				font-size: 1.3rem;
				color: #fff;
				cursor: pointer;
				transition: 0.2s;
		}

		.section-1 a:hover{
				color: #fff;
				cursor: pointer;
				transition: 0.3s;
		}

		.white:hover{
				position: relative;
				padding-left: 10px;
		}

		/* media queres */
		@media(max-width:780px){
				.grid-2{
						grid-template-columns: 1fr;
				}
				.section-1{
						padding:0;
						padding-top: 5rem;
				}
				.section-2{
						padding: 0;
						padding-left: 1.5rem;
						padding-top: 2rem;
				}
		}
		
		img {
			border-radius: 10px;
			border: 5px solid #ddd;
		}
	
	</style>
</head>
<body>
	<div class="grid-2">
		<div class="section-1">
				<i class="fas fa-code fa-5x white"></i>
				<h2>Project Odyssey</h2>
				<p>Brisbane, Australia.</p>
				<a href="https://twitter.com/rickastley" target="_blank">
					<i class="fab fa-twitter"></i>
				</a>
				<a href="https://www.linkedin.com/in/rick-astley-b6a42b24/" target="_blank">
					<i class="fab fa-linkedin"></i>
				</a>
				<a href="https://github.com/woflydev/odyssey_cnn" target="_blank">
					<i class="fab fa-github"></i>
				</a>
		</div>
		<div class="section-2">
		
				<img src="stream.mjpg" width="320" height="240" /> 
		
				<!--<h2>About</h2>
				<p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Perferendis quas sint et nihil iusto eius nostrum sit error, repellat optio quisquam! Magnam dolore iusto cumque. Nostrum error iste neque maiores.</p>
				<h2>Experience</h2>
				<p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Reiciendis in maiores autem quidem.</p>

				<h2>Skills</h2>
				<p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Reiciendis in maiores autem quidem obcaecati excepturi! Cupiditate eaque itaque magni voluptatibus neque nobis est dolor? Atque sunt minus ipsa asperiores. At.</p>
				<h2>Projects</h2>
				<a href="#">Project 1</a>
				<a href="#">Project 2</a>
				<a href="#">Project 3</a>
				<a href="#">Project 4</a>
				<a href="#">Project 5</a>-->
				<h2>Contact</h2>
				<p>wolfy.coding@email.com</p>
		</div>
	</div>
</body>
</html>

"""

class StreamingHandler(server.BaseHTTPRequestHandler):
		def do_GET(self):
				if self.path == '/':
					self.send_response(301)
					self.send_header('Location', '/index.html')
					self.end_headers()
				elif self.path == '/index.html':
					content = PAGE.encode('utf-8')
					self.send_response(200)
					self.send_header('Content-Type', 'text/html')
					self.send_header('Content-Length', len(content))
					self.end_headers()
					self.wfile.write(content)
				elif self.path == '/stream.mjpg':
					self.send_response(200)
					self.send_header('Age', 0)
					self.send_header('Cache-Control', 'no-cache, private')
					self.send_header('Pragma', 'no-cache')
					self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
					self.end_headers()
					try:
						while True:
							frame = camera.read_frame()
							ret, frame = cv2.imencode('.jpg', frame)
							self.wfile.write(b'--FRAME\r\n')
							self.send_header('Content-Type', 'image/jpeg')
							self.send_header('Content-Length', len(frame))
							self.end_headers()
							self.wfile.write(frame)
							self.wfile.write(b'\r\n')
					except Exception as e:
						logging.warning(
								'Removed streaming client %s: %s',
								self.client_address, str(e))
				else:
					self.send_error(404)
					self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
		allow_reuse_address = True
		daemon_threads = True

def start_streaming():
	address = ('', 8000)
	server = StreamingServer(address, StreamingHandler)
	server.serve_forever()

def begin_thread():
	stream_thread = Thread(target=start_streaming, args=(), daemon=True)
	stream_thread.start()

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	while True:
		camera.init()
		address = ('', 8000)
		server_handle = StreamingServer(address, StreamingHandler)
		try:
			server_handle.serve_forever()
		except KeyboardInterrupt:
			logging.warning("Keyboard Interrupt! Press any key to continue or 'q' to quit...")
			camera.stop()
			x = input()
			if x == "q":
				server_handle.shutdown()
				break
			continue