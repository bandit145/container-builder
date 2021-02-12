from abc import ABC, abstractmethod


#Resolution strategies come in after a build has completed with various ways to determine
# when a pushable change has occured

class Strategy(ABC):

	@abstractmethod
	def compare(self, new_img, img):
		pass


class Branch(Strategy):

	def __init__(self):
			super().___init__()

	def compare(self, new_img, img):
		return new_img.id == img.id



track_branch = Branch


