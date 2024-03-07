# A Movie rating and recommendation system

## Installing the requirements 

To build the component, [`componentize-py`](https://pypi.org/project/componentize-py/) and [`spin-sdk`](https://pypi.org/project/spin-sdk/) are required. To install them, run:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Setup numpy

Note that we use an unofficial build of NumPy since the upstream project does not yet publish WASI builds.

```bash
curl -OL https://github.com/dicej/wasi-wheels/releases/download/v0.0.1/numpy-wasi.tar.gz
tar xf numpy-wasi.tar.gz
```

## Builing and Running

```
spin up --build --sqlite @migrations.sql
```

### Populating the sqlite database

Use the `populate_dd.sh` to put movies and ratings into the database. 

```bash
./populate_db.sh
```

### Querying for Statistics about a movie

```bash
curl "localhost:3000/calculate_movie_ratings?movie_id=1"
```

### Querying for Suggesstions Based on Similar Users

```bash
curl "localhost:3000/movie_recommendations?user_id=1"
```