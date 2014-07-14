import helpers

class EndpointAddress(str):
    """
    A valid network address for one of the components of the pipeline pattern to either bind to or connect to.

    The supported protocols are:
        - tcp for cross-machine communication
        - ipc for cross-process communication
        - inproc for cross-thread communication

    Note that on unix systems cross-process sockets are files, as it recommended to specify the .ipc file extension
    when naming ipc socket addresses.
    """
    def __init__(self, address):
        self.name = None
        if not helpers.valid_endpoint(self):
            raise AttributeError('Address %s is not a valid endpoint' % self)

    def __set__(self, instance, value):
        raise AttributeError('Cannot update an EndpointAddress object')
    def __delete__(self, instance):
        raise AttributeError('Cannot delete an EndpointAddress object')


class BaseEnum(str):
    """
    Base class for enumerations. You must subclass and provide
    values for the _valid list.
    """
    _enums = set()

    def __init__(self, v):
        if self not in self._enums:
            raise TypeError('Invalid option: %s' % self)

    @staticmethod
    def IsValid(v):
        return v in BaseEnum._enums



class TaskType(BaseEnum):
    """
    Represents a task type.

    A task type is any valid string that has been previously registered with the TaskType class.
    Unregistered task types will raise an exception.
    """
    ALL_TASK_TYPES = set()

    @classmethod
    def register_type(cls, task_type):
        cls.ALL_TASK_TYPES.add(task_type)

    @property
    def _enums(self):
        return [''] + list(TaskType.ALL_TASK_TYPES)

