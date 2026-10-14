def merge_sort(items,key, reverse=False):
    if len(items) <= 1:
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key, reverse)
    right = merge_sort(items[middle:], key, reverse)
    return merge(left, right, key, reverse)
def merge(left, right, key, reverse):
    result = []
    i = 0
    j =0
    while i < len(left) and j < len(right):
        if goes_first(key(left[i]), key(right[j]), reverse):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    while i < len(left):
        result.append(left[i])
        i += 1
    while j < len(right):
        result.append(right[j])
        j += 1
    return result


def goes_first(a, b, reverse):
    if a is None:
        return b is None
    if b is None:
        return True
    if reverse:
        return a >= b
    return a <=b