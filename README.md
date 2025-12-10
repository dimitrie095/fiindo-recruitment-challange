
# Fiindo ETL Project – Setup & Run Instructions

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/dimitrie095/fiindo-recruitment-challange
cd fiindo-recruitment-challange
```


### 2. Install Dependencies (Local Run)

(Optional if you use Docker)

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

- Windows:

```bash
venv\Scripts\activate
```

- macOS/Linux:

```bash
source venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configure API

Open:

```
src/config.py
```

Set:

```python
API_BASE_URL = "https://api.test.fiindo.com/api/v1"
API_AUTH_TOKEN = "Bearer firstname.lastname"
```

---

## ▶️ Run the Application (Local)

```bash
python -m src.main
```

---

# 🐳 Run with Docker

### 1. Build the Image

```bash
docker build -t fiindo-etl .
```

### 2. Run the Container

```bash
docker run -u -m fiindo-etl
```

---

# 🐳 Run with Docker Compose

```bash
docker-compose up --build
```

---

# 🧪 Run Unit Tests

Local:

```bash
pytest
```

Docker:

```bash
docker run -u -m  fiindo-etl pytest
```

---

# 🗄 Database

- SQLite database file is stored inside the project or container.
- You can mount it using docker-compose for persistence.




