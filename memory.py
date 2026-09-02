import json
import os

MEMORY_FILE = "memory.json"


# ==========================
# LOAD MEMORY
# ==========================

def load_memory():

    if not os.path.exists(MEMORY_FILE):

        with open(MEMORY_FILE, "w") as file:
            json.dump({}, file, indent=4)

    with open(MEMORY_FILE, "r") as file:

        return json.load(file)


# ==========================
# SAVE MEMORY
# ==========================

def save_memory(memory):

    with open(MEMORY_FILE, "w") as file:

        json.dump(memory, file, indent=4)


# ==========================
# REMEMBER
# ==========================

def remember(key, value):

    memory = load_memory()

    memory[key] = value

    save_memory(memory)


# ==========================
# RECALL
# ==========================

def recall(key):

    memory = load_memory()

    return memory.get(key)


# ==========================
# FORGET
# ==========================

def forget(key):

    memory = load_memory()

    if key in memory:

        del memory[key]

        save_memory(memory)


# ==========================
# SHOW EVERYTHING
# ==========================

def all_memories():

    return load_memory()