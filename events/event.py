import asyncio

class AsyncEvent:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    async def fire(self, *args, **kwargs):
        coroutines = [handler(*args, **kwargs) for handler in self.handlers]
        await asyncio.gather(*coroutines)