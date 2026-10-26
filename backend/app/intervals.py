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

def overlapChecker(classBlocks, practiceBlock):
    """Check if blocks overlap
    
        classBlocks: a list of (start, end) tuples
        practiceBlock: a (start, end) tuple
        Returns True if any classblock overlaps the practice block otherwise False
        """

    practice_start, practice_end = practiceBlock

    for class_start, class_end in classBlocks:

        #two ranges overlap if each start is before the end of the other, one block ending when a separate block starts is not an overlap
        #think of it as a time line, you cant have two starts back to back, it must go start end start end...
        if(class_start < practice_end or practice_start < class_end):
            return True
        
    return False

if __name__ == "__main__":
    #can use plain numbers to test since datetime Objs allow the same operators
    #plain numbers wont support days of the week however the datetime obj will handel that for us
    #it understands mondy is before tuesday
    assert mergeBlocks([]) == []
    assert mergeBlocks([(9, 10)]) == [(9, 10)]
    assert mergeBlocks([(9, 10), (11, 12)]) == [(9, 10), (11, 12)]
    assert mergeBlocks([(9, 11), (10, 12)]) == [(9, 12)]
    assert mergeBlocks([(9, 10), (10, 11)]) == [(9, 11)]
    assert mergeBlocks([(13, 14), (9, 10)]) == [(9, 10), (13, 14)]
    assert mergeBlocks([(9, 12), (10, 11)]) == [(9, 12)]
    assert mergeBlocks([(9, 10), (9.5, 11), (10.5, 12)]) == [(9, 12)]
    #check that original is unchanged
    original = [(13, 14), (9, 10)]
    mergeBlocks(original)
    assert original == [(13, 14), (9, 10)], "merge_blocks modified its input"

    assert overlapChecker([(9,11)],(15,17)) == False
    assert overlapChecker([(15,17)],(9,11)) == False
    #class ending right when practice starts is acceptable and you can be included in that practice
    assert overlapChecker([(9,11)],(11,13)) == False
    assert overlapChecker([(9,16)],(11,13)) == True
    assert overlapChecker([(9,16)],(8,13)) == True

    assert overlapChecker([(9,11),(15,17),(9,11)],(11,13)) == False
    assert overlapChecker([(9,11)],(1,3)) == False
    assert overlapChecker([(9,11)],(7,9)) == False

    # class fully inside the practice
    assert overlapChecker([(11.5, 12.5)], (11, 13)) == True
    # identical times
    assert overlapChecker([(11, 13)], (11, 13)) == True
    # same start, class ends earlier
    assert overlapChecker([(11, 12)], (11, 13)) == True


    print("All checks passed!")