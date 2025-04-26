class ModelUploadError(Exception):
    pass

class RabbitMQError(Exception):
    def __init__(self, description: str):
        self.description = description
        super().__init__(description)

    def __str__(self):
        return f"RabbitMQError: {self.description}"