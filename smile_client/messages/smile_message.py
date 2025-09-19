class SmileMessage(object):

    def __init__(self, subject, data):
        self.subject = subject
        self.data = data

    def __str__(self):
        return f"SmileMessage: {self.subject} {self.data}"