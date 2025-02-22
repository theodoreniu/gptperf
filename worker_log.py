import os
from time import sleep
import redis
from dotenv import load_dotenv
load_dotenv()

host = os.getenv("REDIS_HOST", 'localhost')
port = os.getenv("REDIS_PORT", 6379)
pwd = os.getenv("REDIS_PWD", "")


if __name__ == "__main__":

    r = redis.Redis(host=host, port=port, db=0)

    while (True):

        r.set('foo', 'bar')
        sleep(1)
        print(r.get('foo'))

        sleep(5)
