import os
from mem0 import MemoryClient

client = MemoryClient(api_key="m0-Nv2d5M2z7fLAVWKyLyO6t3pImEi9Q96bMqFt0xL7")

user_memories = client.get_all(user_id="TestStudent")
for i in user_memories:
    print(i['memory'])
