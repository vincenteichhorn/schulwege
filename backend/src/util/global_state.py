import asyncio
import json
from pathlib import Path

import aiofiles


ALLOWED_TYPES = (int, float, str, bool, type(None))  # only "atomic" types


class GlobalState:
    _instance = None
    _init_lock = asyncio.Lock()
    _state_lock = asyncio.Lock()

    def __init__(self):
        self.state = {}

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            async with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._async_init()
        return cls._instance

    async def _async_init(self):
        self.state = {}

    async def contains(self, key):
        async with self._state_lock:
            parts = key.split(".")
            d = self.state
            for part in parts:
                if not isinstance(d, dict) or part not in d:
                    return False
                d = d[part]
            return True

    async def get(self, key, default=None):
        if not await self.contains(key):
            return default
        async with self._state_lock:
            parts = key.split(".")
            d = self.state
            for part in parts:
                if not isinstance(d, dict):
                    return default
                d = d.get(part, default)
                if d is default:
                    break
            return d

    async def set(self, key, value):
        if not isinstance(value, ALLOWED_TYPES):
            raise TypeError(f"Value must be an atomic type ({ALLOWED_TYPES})")
        async with self._state_lock:
            parts = key.split(".")
            d = self.state
            for part in parts[:-1]:
                if part not in d or not isinstance(d[part], dict):
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = value

    async def load_from_json(self, filepath):
        """Load state from a JSON file"""
        if not Path(filepath).exists():
            return
        async with aiofiles.open(filepath, "r") as f:
            data = json.loads(await f.read())
        await self._load_dict(data)

    async def save_to_json(self, filepath):
        """Save state to a JSON file"""
        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(self.state, indent=4))

    async def _load_dict(self, data, parent_key=""):
        """Recursively load dictionary into state"""
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                await self._load_dict(value, full_key)
            elif isinstance(value, ALLOWED_TYPES):
                await self.set(full_key, value)
            else:
                print(f"Skipping non-atomic value for {full_key}: {type(value)}")
