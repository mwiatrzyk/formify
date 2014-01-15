from formify import exc


class ValidateMethodMixin(object):

    def validate(self, value):
        pass


class LengthValidationMixin(ValidateMethodMixin):

    def validate(self, value):
        super(LengthValidationMixin, self).validate(value)
        if self.min_length is not None and self.max_length is not None:
            self.__validate_length_range(value)
        elif self.min_length is not None:
            self.__validate_min_length(value)
        elif self.max_length is not None:
            self.__validate_max_length(value)

    def __validate_length_range(self, value):
        if not self.min_length <= len(value) <= self.max_length:
            raise exc.ValidationError('length_out_of_range',
                min_length=self.min_length,
                max_length=self.max_length)

    def __validate_min_length(self, value):
        if len(value) < self.min_length:
            raise exc.ValidationError('too_short', min_length=self.min_length)

    def __validate_max_length(self, value):
        if len(value) > self.max_length:
            raise exc.ValidationError('too_long', max_length=self.max_length)
