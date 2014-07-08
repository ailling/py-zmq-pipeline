import helpers

class EndpointAddress(str):
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
    ALL_TASK_TYPES = set()

    @classmethod
    def register_type(cls, task_type):
        cls.ALL_TASK_TYPES.add(task_type)

    @property
    def _enums(self):
        return [''] + list(TaskType.ALL_TASK_TYPES)

