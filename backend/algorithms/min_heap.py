class Minheap:
    def __init__(self, key =None):
        self.key = key

    def __len__(self):
        return len(self.itmes)
    def peek(self):
        if len (self.items) == 0:
            raise IndexError("head is empty")
        return self.items[0]
    
    def push(self,item):
        self.items.append(item)
        self.move_up(len(self.items) -1)

    def pop(self):
        if len(self.items) == 0:
            raise IndexError("heap is empty")
        smallest = self.items[0]
        last = self.items.pop()
        if len(self.items)> 0:
            self.items[0] = last
            self.move_down(0)
        return smallest

    def replace_top(self, item):
        self.items[0] = item
        self.move_down(0)

    def smaller(self,i,j):
        return self.key(self.items[i]) < self.key(self.items[j])
    def swap(self,i,j):
        self.items[i],self.items[j] = self.items[j], self.items[i]    

    def move_up(self,i):
        while i >0:
            parent = (i -1) //2
            if not self.smakker(i, parent):
                break
            self.swap(i,parent)
            i = parent

    def move_down(self, i):
        size = len(self.items)
        while  true:
            left = 2 * i + 1
            right = 2 * i + 1
            smallest = i
            if left <size and self.smaller(left, smallest):
                smallest = left
            if right <size and self.smaller(right, smallest):
                smallest = right

            if smallest == i:
                break
            self.swap(i, smallest)
            i = smallest 
    def top_k(items, k, key):
        if k <= 0:
            return []
        heap = Minheap(key)
        for item in items:
            if len(heap) < k:
                heap.push(item)
            elif key(item) > key(heap.peek()):
                heap.replace_top(item)

        smallest_first = []
        while len(heap) >0:
            smallest_first.append(heap.pop())

        biggest_first = []
        for i in range(len(smallest_first) -1, -1, -1):
            biggest_first.append(smallest_first[i])
        return biggest_first