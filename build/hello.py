import os
print(os.getenv("DOMAIN"))
import os
env_vars = os.environ
for key, value in env_vars.items():
    print(f"{key}: {value}")
for i in range(10):
    print(i)


def handler(event, context):
    print(event)
