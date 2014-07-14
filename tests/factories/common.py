import factory
import inspect


class FlexibleObjectFactory(factory.Factory):
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if hasattr(model_class, '__init__') and type(model_class.__init__).__name__ != 'wrapper_descriptor':
            fargs = inspect.getargspec(model_class.__init__)
            arglist = []

            if fargs.varargs and fargs.keywords:
                model_class(*args, **kwargs)

            for arg in args:
                if not fargs.keywords and arg not in fargs.args:
                    raise Exception('Cannot invoke %s with the parameters passed' % str(model_class))
                arglist.append(arg)

            for arg in fargs.args[1:]:
                if arg in kwargs:
                    arglist.append(kwargs[arg])
                    kwargs.pop(arg)

            if not fargs.args[1:] and not fargs.keywords:
                m = model_class()
            elif fargs.args[1:] and not fargs.keywords:
                m = model_class(*arglist)
            elif not fargs.args[1:] and fargs.keywords:
                m = model_class(**kwargs)
            elif fargs.args[1:] and fargs.keywords:
                m = model_class(*arglist, **kwargs)
            else:
                raise Exception('Cannot instantiate %s' % str(model_class))
        else:
            m = model_class()

        attrs = [a for a in dir(model_class) if '__' not in a]
        for attr in attrs:
            if attr in kwargs:
                setattr(m, attr, kwargs[attr])

        return m


    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return cls._build(model_class, *args, **kwargs)

