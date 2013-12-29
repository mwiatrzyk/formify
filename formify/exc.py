class ConversionError(TypeError):

    def __init__(self, message_id, **params):
        self.message_id = message_id
        self.params = params


class ValidationError(ValueError):

    def __init__(self, message_id, **params):
        self.message_id = message_id
        self.params = params
