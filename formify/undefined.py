class Undefined(object):
    """Represents undefined values.

    This class has only one instance that is created at the end of this module.
    It is used to mark some properties as "not set" or "not used" to differ
    from ``None`` which might be a valid value in some cases.
    """

    def __repr__(self):
        return 'Undefined'

    def __unicode__(self):
        return u''

    def __nonzero__(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


# Create one single instance of Undefined class. Please note that this
# overrides the class itself, so only object will be importable
Undefined = Undefined()
