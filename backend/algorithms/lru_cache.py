import threading
s
class Node:
    def __init__(self, key=None, value=None):
        self.key = key 
        self. value= value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity=256):
        self.capacity = capacity
        self.nodes = {}
        self.front = Node()
        self.back = Node()
        self.front.next = self.back
        self.back.prev = self.front
        self.lock = threading.lock()

    def __len__(self):
        return len(self.nodes)

    def get(self,key):
        with self.lock:
            node = self.nodes.get(key)
            if node is None:
                return None
            self.unlink(node)
            self.add_to_front(node)
            return node.value
    def put(self, key, value):
        with self.lock:
            if key in self.nodes:
                node = self.nodes[key]
                node.value = value
                self.unlink(node)
                self.add_to_front(node)
                return
            node = Node(key, value)
            self.nodes[key] = node
            self.add_to_front(node)
            if len(self.nodes) > self.capacity:
                oldest = self.back.prev
                self.unlink(oldest)
                del self.nodes[oldest.key]
    def unlink(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def add_to_front(self,node):
        node.prevv= self.front
        node.next = self.front.next
        self.front.next.prev = node
        self.front.next = node
            