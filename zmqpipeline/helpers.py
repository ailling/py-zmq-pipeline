from urlparse import urlparse


def valid_endpoint(addr):
    if not addr:
        return False

    parsed = urlparse(addr)
    if parsed.scheme not in ('inproc', 'ipc', 'tcp'):
        return False

    if not parsed.netloc:
        return False

    if parsed.scheme == 'tcp':
        if len(parsed.netloc.split(':')) != 2:
            return False
        host, port = parsed.netloc.split(':')
        if not port.isdigit():
            return False

    return True


def endpoint_binding(addr):
    if not valid_endpoint(addr):
        return TypeError('Attempted to bind to invalid endpoint')

    parsed = urlparse(addr)
    if parsed.scheme == 'tcp':
        host, port = parsed.netloc.split(':')
        return 'tcp://*:%s' % port
    else:
        return addr

