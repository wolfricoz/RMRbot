import enum


class ForumStatus(enum.Enum) :
	APPROVED = "approved"
	NEW = "new"
	BUMP = "bump"

	def __str__(self):
		return self.value