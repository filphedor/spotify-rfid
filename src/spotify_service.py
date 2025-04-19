import time

import requests


class SpotifyService:
	def __init__(self, client_id):
		self.client_id = client_id
		self.token = None
		
	def set_token(self, token):
		self.token = token

	def refresh_token(self):
		try:
			url = 'https://accounts.spotify.com/api/token'

			headers = {
				'Content-Type': 'application/x-www-form-urlencoded'
			}

			data = {
				'grant_type': 'refresh_token',
				'refresh_token': self.token.get('refresh_token'),
				'client_id': self.client_id
			}

			response = requests.post(url, headers=headers, data=data)


			if response.ok:
				new_token = response.json()
				self.token = new_token
			else:
				raise Exception('Refresh request unsuccessful: ' + response.text)

		except Exception as e:
			raise Exception('Failed to refresh token') from e

	def get_headers(self):
		return {
			'Authorization': 'Bearer ' + self.token.get('access_token')
		}

	def wrap_with_auth_try(self, f):
		try:
			response = f()

			return response
		except Exception as e:
			try:
				self.refresh_token()
				response = f()

				return response
			except Exception as e2:
				raise Exception('Request error') from e2

	def get_queue(self):
		def get_queue_call():
			url = 'https://api.spotify.com/v1/me/player/queue'

			response = requests.get(url, headers=self.get_headers())

			if response.ok:
				return response
			else:
				raise Exception('Get queue unsuccessful: ' + str(response.status_code))

		response = self.wrap_with_auth_try(get_queue_call)

		data = response.json()

		return data

	def add_item_to_queue(self, uri):
		def add_item_call():
			url = 'https://api.spotify.com/v1/me/player/queue'

			params = {
				'uri': uri
			}

			response = requests.post(url, headers=self.get_headers(), params=params)

			if response.ok:
				return response
			else:
				raise Exception('Add unsuccessful: ' + str(response.status_code))

		self.wrap_with_auth_try(add_item_call)

		return

	def skip(self):
		def skip_call():
			url = 'https://api.spotify.com/v1/me/player/next'

			response = requests.post(url, {}, headers=self.get_headers())

			if response.ok:
				return response
			else:
				raise Exception('Skip unsuccessful' + str(response.status_code))

		self.wrap_with_auth_try(skip_call)

		return 
	
	def get_album_tracks(self, uri):
		def get_tracks_call():
			album_id = uri.split(':')[2].strip()
			
			url = 'https://api.spotify.com/v1/albums/' + album_id + '/tracks'

			params = {'limit': 50}

			response = requests.get(url, headers=self.get_headers(), params=params)

			if response.ok:
				return response
			else:
				raise Exception('Get tracks unsuccessful: ' + str(response.status_code))

		response = self.wrap_with_auth_try(get_tracks_call)

		data = response.json()

		return data.get('items')
	

	def wait_for_queue_change(self, orig_queue):
		tries = 0
		current_queue = orig_queue

		while tries < 5 and current_queue == orig_queue:
			current_queue = self.get_queue()

			tries = tries + 1
			time.sleep(1)


	def ensure_skip(self):
		orig_queue = self.get_queue()

		self.skip()

		self.wait_for_queue_change(orig_queue)


	def clear_queue_to_song(self, uri):
		is_queue_empty = False

		while(not is_queue_empty):
			queue = self.get_queue()

			if queue.get('currently_playing') != None:
				if queue.get('currently_playing').get('uri') == uri:
					return
				else:
					self.ensure_skip()

			else:
				return


	def add_item_to_queue_with_wait(self, uri):
		orig_queue = self.get_queue()

		self.add_item_to_queue(uri)

		self.wait_for_queue_change(orig_queue)

		return
	

	def add_album_to_queue(self, uri):
		tracks = self.get_album_tracks(uri)

		for track in tracks:
			print(track)
			self.add_item_to_queue_with_wait(track.get('uri'))

	def play_item(self, uri):
		try:
			self.add_album_to_queue(uri)
			
			first_uri = self.get_album_tracks(uri)[0].get('uri')

			self.clear_queue_to_song(first_uri)

		except Exception as e:
			print(e)