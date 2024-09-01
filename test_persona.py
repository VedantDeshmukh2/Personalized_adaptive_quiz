import os
from mem0 import MemoryClient

client = MemoryClient(api_key="KEY")

user_memories = client.get_all(user_id="TestStudent")
for i in user_memories:
    print(i['memory'])
