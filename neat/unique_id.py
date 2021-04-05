class UniqueId:
	def __init__(self, initial_value=0):
		self.num = initial_value

	def next_id(self):
		self.num += 1
		return self.num - 1
