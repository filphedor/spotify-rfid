import requests

class SpotifyService:
	def __init__(self, client_id):
		self.client_id = client_id
		self.token = None
		
	def set_token(self, token):
		self.token = token

	def refresh_token(self):
		url = 'https://accounts.spotify.com/api/token'

		headers = {
			'Content-Type': 'application/x-www-form-urlencoded'
		}

		data = {
			'grant_type': 'refresh_token',
			'refresh_token': self.token.get('refresh_token'),
			'client_id': self.client_id
		}

		try:
			response = requests.post(url, headers=headers, data=data)

			if response.status_code == 200:
				new_token = response.json()
				self.token = new_token

			else:
				raise Exception('Refresh request unsuccessful')

		except:
			raise Exception('Failed to refresh token')

	def get_headers(self):
		return {
			'Authorization': 'Bearer ' + self.token.get('access_token')
		}

	def wrap_with_auth_try(self, f):
		try:
			response = f()
			return response
		except:
			self.refresh_token()
			response = f()
			return response

	def get_queue(self):
		def get_queue_call():
			url = 'https://api.spotify.com/v1/me/player/queue'

			response = requests.get(url, headers=self.get_headers())

			if response.status_code == 200:
				return response
			else:
				raise Exception('Get queue unsuccessful')

		response = self.wrap_with_auth_try(get_queue_call)

		data = response.json()

		return data

	def skip(self):
		def skip_call():
			url = 'https://api.spotify.com/v1/me/player/next'

			response = requests.post(url, {}, headers=self.get_headers())

			if response.status_code == 204:
				return response
			else:
				print(response.status_code)
				print(response.text)
				raise Exception('Skip unsuccessful')

		self.wrap_with_auth_try(skip_call)

		return 


	def clear_queue_to_song(self, uri):
		is_queue_empty = False

		while(not is_queue_empty):
			queue = self.get_queue()

			if queue.get('currently_playing') != None:
				if queue.get('currently_playing').get('uri') == uri:
					return
				else:
					self.skip()

			else:
				return


	def add_item_to_queue(self, uri):
		def add_item_call():
			url = 'https://api.spotify.com/v1/me/player/queue'

			params = {
				'uri': uri
			}

			response = requests.post(url, headers=self.get_headers(), params=params)

			if response.status_code == 204:
				return response
			else:
				print(response.status_code)
				print(response.text)
				raise Exception('Add unsuccessful')

		self.wrap_with_auth_try(add_item_call)

		return
	
	def get_album_tracks(self, uri):
		def get_tracks_call():
			album_id = uri.split(':')[2].strip()
			
			print(album_id)
			
			url = 'https://api.spotify.com/v1/albums/' + album_id + '/tracks'

			params = {'limit': 50}

			response = requests.get(url, headers=self.get_headers(), params=params)

			if response.status_code == 200:
				return response
			else:
				raise Exception('Get tracks unsuccessful')

		response = self.wrap_with_auth_try(get_tracks_call)

		data = response.json()

		return data.get('items')

	def add_album_to_queue(self, uri):
		tracks = self.get_album_tracks(uri)

		for track in tracks:
			self.add_item_to_queue(track.get('uri'))

	def play_item(self, uri):
		try:
			self.add_album_to_queue(uri)
			
			first_uri = self.get_album_tracks(uri)[0].get('uri')

			self.clear_queue_to_song(first_uri)

		except Exception as e:
			print(e)