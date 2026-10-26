#Merge overlaping blocks

def mergeBlocks(blocks):
    """Merge overlapping or touching time blocks.

    blocks: a list of (start, end) tuples, in any order.
    Returns a new list of (start, end) tuples, sorted by start,
    where no two blocks overlap or touch.
    """
    blocks = sorted(blocks)

    result = []

    for start, end in blocks:
        if(len(result) == 0):
            result.append((start, end))
            continue

        previousStart, previousEnd = result[-1]
        if (previousEnd >= start):
            result.pop()
            end = max(end, previousEnd)
            result.append((previousStart, end))
            continue

        result.append((start, end))

    return result

if __name__ == "__main__":
    assert mergeBlocks([]) == []
    assert mergeBlocks([(9, 10)]) == [(9, 10)]
    assert mergeBlocks([(9, 10), (11, 12)]) == [(9, 10), (11, 12)]
    assert mergeBlocks([(9, 11), (10, 12)]) == [(9, 12)]
    assert mergeBlocks([(9, 10), (10, 11)]) == [(9, 11)]
    assert mergeBlocks([(13, 14), (9, 10)]) == [(9, 10), (13, 14)]
    assert mergeBlocks([(9, 12), (10, 11)]) == [(9, 12)]
    assert mergeBlocks([(9, 10), (9.5, 11), (10.5, 12)]) == [(9, 12)]
    
    original = [(13, 14), (9, 10)]
    mergeBlocks(original)
    assert original == [(13, 14), (9, 10)], "merge_blocks modified its input"
    print("All checks passed!")