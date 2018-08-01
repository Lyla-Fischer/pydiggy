class ConflictingType(AttributeError):
    def __init__(self, pname, incoming, existing):
        incoming_name = getattr(incoming, "__name__", repr(incoming))
        existing_name = getattr(existing, "__name__", repr(existing))

        msg = f"You previously defined {pname} as {existing_name}. " \
            f"You cannot now define it as {incoming_name}."

        super().__init__(msg)


class NotStaged(AttributeError):
    def __init__(self, uid):
        msg = f"Cannot generate with unstaged reference {uid}. " \
            "Did you forget to call <node>.stage()"

        super().__init__(msg)


class InvalidData(Exception):
    def __init__(self, msg=''):
        msg = f"Data in invalid format. {msg}"

        super().__init__(msg)
