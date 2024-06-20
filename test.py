def test(x, sync = False):

    print('hello world')

    if sync:
        return 5

    return 4*x

ans = test(6, sync=False)
print(ans)