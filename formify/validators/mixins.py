from formify import exc


class ValidatorMixin(object):

    def validate(self, value):
        pass


class LengthValidatorMixin(ValidatorMixin):

    def validate(self, value):
        super(LengthValidatorMixin, self).validate(value)
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


class ValueValidatorMixin(ValidatorMixin):

    def validate(self, value):
        super(ValueValidatorMixin, self).validate(value)
        if self.min_value is not None and self.max_value is not None:
            self.__validate_value_range(value)
        elif self.min_value is not None:
            self.__validate_min_value(value)
        elif self.max_value is not None:
            self.__validate_max_value(value)

    def __validate_value_range(self, value):
        if not self.min_value <= value <= self.max_value:
            raise exc.ValidationError('value_out_of_range',
                min_value=self.min_value, max_value=self.max_value)

    def __validate_min_value(self, value):
        if value < self.min_value:
            raise exc.ValidationError('too_low', min_value=self.min_value)

    def __validate_max_value(self, value):
        if value > self.max_value:
            raise exc.ValidationError('too_high', max_value=self.max_value)
