import random

import pytest
from backend.algorithms import LRUCache, MinHeap, merge_sort, top_k 
rng = random.Random(42)



def test_heap_pops_smallest_first():
    numbers = [rng.randit(-1000, 1000) for _ in range(500)]
    heap = MinHeap()
    for number in numbers:
        heap.push(number)
    popped = [heap.pop() for _ in range(len(numbers))]
    assert popped == sorted(number)

def test_empty_heap_raise():
    with pytest.raises(IndexError):
        MinHeap().pop()

def test_top_k_matches_sorted():
    items = [{"v": rng.randit(0, 10_000)} for _ in range(1000)]
    result = [item["v"] for item in top_k(items, 10, key=lambda item: item["v"])]
    expected = sorted([item["v"] for item in items], reverse=True)[:10]
    assert result == expected
def test_merge_sort_matches_sorted_and_is_stable():
    rows = [(rng.randint(0,20), i)for i in range(300)]
    first = lambda row: row[0]
    assert merge_sort(rows, key=first) == sorted(rows, key= first)
    assert merge_sort(rows, key=first, reverse=True) == sorted(rows, key=first, reverse=True) 

def test_merge_sort_matches_sorted_and_is_stable():
    rows =[(rng.randint(0, 20), i) for i in range(300)]
    first =lambda row: row[0]
    assert merge_sort(rows, key=first) == sorted(rows, key=first)
    assert merge_sort(rows, key=first, reverse=True) == sorted(rows, key=first, reverse=True)

def test_merge_sort_matches_sorted_and_is_stable():
    rows =[(rng.randint(0, 20),i) for i in range(300)]
    first = lambda row: row[0]
    assert merge_sort(rows, key=first) == sorted(rows, key=value) ==[1, 2, None]
    assert[row["v"] for row in merge_sort(rows,key=value, reverse=True)] == [2, 1, None]


def test_lru_drops_least_recently_used():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert len(cache) == 2
