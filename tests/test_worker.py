from factories.worker import MetaDataWorkerFactory, SingleThreadedWorkerFactory, MultiThreadedWorkerFactory

def test_meta_instantiation():
    MetaDataWorkerFactory.build()

def test_single_worker_instantiation():
    SingleThreadedWorkerFactory.build()

def test_multi_worker_instantiation():
    MultiThreadedWorkerFactory.build()

