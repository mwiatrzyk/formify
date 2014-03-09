# formify/validators/mixins.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

from formify import exc

from formify.validators.base import BaseValidator


class LengthValidationMixin(BaseValidator):
    """Mixin class suplying validator with value length validation.

    This mixin requires validator that inherits from it to have two additional
    properties:

    ``min_length``
        for minimal accepted length of value (inclusive)

    ``max_length``
        for maximal accepted length of value (inclusive)

    Default value for each should be ``None``.
    """

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
            raise exc.ValidationError('value_length_out_of_range',
                min_length=self.min_length,
                max_length=self.max_length)

    def __validate_min_length(self, value):
        if len(value) < self.min_length:
            raise exc.ValidationError('value_too_short', min_length=self.min_length)

    def __validate_max_length(self, value):
        if len(value) > self.max_length:
            raise exc.ValidationError('value_too_long', max_length=self.max_length)


class RangeValidationMixin(BaseValidator):
    """Mixin class suplying validator with value range validation.

    This mixin requires validator that inherits from it to have two additional
    properties:

    ``min_value``
        for minimal accepted value (inclusive)

    ``max_value``
        for maximal accepted value (inclusive)

    Default value for each should be ``None``.
    """

    def validate(self, value):
        super(RangeValidationMixin, self).validate(value)
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
            raise exc.ValidationError('value_too_low', min_value=self.min_value)

    def __validate_max_value(self, value):
        if value > self.max_value:
            raise exc.ValidationError('value_too_high', max_value=self.max_value)
