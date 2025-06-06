
import os
from time import sleep
from threading import Thread, Lock

from flask import Flask, request
from flask_cors import CORS

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

from spotify_service import SpotifyService

reader = SimpleMFRC522()

app_spotify_service = SpotifyService(os.environ['SPOTIFY_CLIENT_ID'])


app = Flask(__name__)
CORS(app)

rfid_lock = Lock()

def check_for_tag():
	try:
		with rfid_lock:
			id, text = reader.read_no_block()
	except:
		print('Read failed')

	return text

def read_loop():
	last_read = None

	while(True):
		current = check_for_tag()

		if current != None and current != last_read:
			try:
				app_spotify_service.play_item(current)
				last_read = current
			except:
				print('Playing item failed')

		sleep(1)

@app.route('/write', methods=['POST'])
def write():
	data = request.json

	id = data.get('id', None)

	if id == None:
		return "Need album id", 400
	try:
		with rfid_lock:
			reader.write(id)
			return "", 201
	except:
		return "Couldn't write", 500


@app.route('/is-connected', methods=['GET'])
def test_connection():
	try:
		app_spotify_service.get_queue()

		return 'OK', 200
	except Exception:
		return "Can't communicate with Spotify", 500

@app.route('/auth', methods=['POST'])
def auth():
	data = request.json
	
	app_spotify_service.set_token(data)

	return 'OK', 200

try:
	thread = Thread(target=read_loop)
	thread.start()
finally:
	GPIO.cleanup()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000, ssl_context=('./ssl/cert.crt', './ssl/key.key'))

