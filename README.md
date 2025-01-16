# GPT Performance Test

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Set up environment variables

Copy and set up the environment variables.

```bash
cp .env.example .env
```

## 3. Run

```bash
python py.py {request_total} {num_threads}
```

If you request 1000000 requests and 10 threads, you can run the following command:  

```bash
python py.py 1000000 10
```

## 4. Check Reports

You can find the reports in the `reports` directory.
