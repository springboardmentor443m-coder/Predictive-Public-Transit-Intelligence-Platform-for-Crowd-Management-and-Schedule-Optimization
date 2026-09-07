sio = None


def set_sio(instance) -> None:
    global sio
    sio = instance


def get_sio():
    return sio
