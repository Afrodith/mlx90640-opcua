import threading
from collections import deque
from typing import Any, List

class CircularBuffer:
    def __init__(self, buffer_size: int = 10):
        """
        Initialize a thread-safe circular buffer with a fixed maximum size

        """
        self.buffer = deque(maxlen=buffer_size)  # Fixed-size buffer
        self.lock = threading.Lock()
        self.is_filled = threading.Event()  # Event to signal when buffer is full
        self.buffer_size = buffer_size  # Store buffer size for reference
    
    def put(self, item: Any) -> bool:
        """
        Add an item to the buffer, overwriting oldest if full
        """
        with self.lock:
            was_full = len(self.buffer) == self.buffer.maxlen
            self.buffer.append(item)  # Automatically removes oldest if full
            
            if not was_full and len(self.buffer) == self.buffer.maxlen:
                self.is_filled.set()  # Signal that buffer is filled
            
            return True
    
    def get(self) -> Any:
        """
        Remove and return an item from the buffer
        """
        with self.lock:
            if self.buffer:
                item = self.buffer.popleft()
                
                # Optional: Clear filled flag if buffer is no longer full
                if len(self.buffer) < self.buffer.maxlen:
                    self.is_filled.clear()
                
                return item
            return None
    
    def get_all(self) -> List[Any]:
        """
        Get all items from the buffer and clear it

        """
        with self.lock:
            items = list(self.buffer)
            self.buffer.clear()
            self.is_filled.clear()
        return items
    
    def peek_all(self) -> List[Any]:
        """
        Get all items from the buffer without removing them
        
        """
        with self.lock:
            return list(self.buffer)
    
    def empty(self) -> bool:
        """
        Check if the buffer is empty

        """
        with self.lock:
            return len(self.buffer) == 0
        
    def full(self) -> bool:
        """
        Check if the buffer is full
        
        """
        with self.lock:
            return len(self.buffer) == self.buffer.maxlen
    
    def qsize(self) -> int:
        """
        Return the current size of the buffer

        """
        with self.lock:
            return len(self.buffer)
    
    def wait_until_filled(self, timeout: float = None) -> bool:
        """
        Wait until the buffer is filled or timeout occurs
        
        """
        return self.is_filled.wait(timeout)
    
    def is_buffer_filled(self) -> bool:
        """
        Check if buffer has been filled to capacity
 
        """
        return self.is_filled.is_set()