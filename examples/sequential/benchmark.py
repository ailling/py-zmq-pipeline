import time

def main(n, delay):
    print 'running - iterations: %d - delay: %.3f' % (n, delay)

    start = time.time()

    for i in xrange(n):
        time.sleep(delay)

    m = (time.time() - start) * 1000
    expected = n * delay * 1000
    overhead = m / expected - 1.0
    print 'expected execution time: %.1f' % expected
    print 'sequential execution took: %.1f milliseconds' % m
    print 'overhead: %.1f%%' % (overhead * 100.0)

if __name__ == '__main__':
    main(100, .01)
    main(1000, .01)
    main(5000, .01)

