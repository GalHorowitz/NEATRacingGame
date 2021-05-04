class UniqueId:
	"""
	A class used for assigning unique IDs
	"""

	def __init__(self, initial_value=0):
		self.num = initial_value

	def next_id(self):
		"""
		Returns the next avaiable ID
		"""

		self.num += 1
		return self.num - 1
