from factories.distributor import DistributorFactory, COLLECTOR_ACK_ENDPOINT, COLLECTOR_ENDPOINT


def test_instantiation():
    DistributorFactory.build()
    DistributorFactory.create()
    assert True


