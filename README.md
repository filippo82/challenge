# Challenge

## Create environment
```shell
git clone git@github.com:filippo82/squirro_challenge.git
python -m venv squirro-env
source squirro-env/bin/activate
pip install -r requirements.txt
export NYT_API_KEY=YOUR_API_KEY
```

## Python 2

```shell
docker build -f Dockerfile_py2 --tag challenge_py2 .
docker run -it -p 8050:8050 --env NYT_API_KEY=$NYT_API_KEY challenge_py2 /bin/bash
python nytimes_filippo_py2.py --api $NYT_API_KEY --query Obama --fq 'news_desk:('Washington')' --max-pages 15 --wait-code429
```

## Python 3
```shell
docker build -f Dockerfile_py3 --tag challenge_py3 .
docker run -it -p 8050:8050 --env NYT_API_KEY=$NYT_API_KEY challenge_py3 /bin/bash
python nytimes_filippo_py3.py --api $NYT_API_KEY --query Obama --fq 'news_desk:('Washington')' --max-pages 15 --wait-code429
```

## Python 3 - Dashboard
```shell
docker run -it -p 8050:8050 --env NYT_API_KEY=$NYT_API_KEY challenge_py3 /bin/bash
python dashboard.py
```
Then point your browser to [http://localhost:8050](http://localhost:8050).