
# Lorcan bet async

## Installation 

Download the project, open it in your text editor, and follow the steps below.

#### Create a virtual environment

```bash
python -m venv venv
```

#### Activate the virtual environment on macOS

```bash
source venv/bin/activate
```

#### Activate the virtual environment on Windows

```bash
venv\Scripts\activate
```

#### Install the project dependencies

```bash
pip install -r requirements.txt
```

Next, create a PostgreSQL database and name it ```lorcan```  or use a name of your choice.

Open the ```.env``` file and update the following values:

```bash
POSTGRES_USER="postgres" # Database username (default is 'postgres')
POSTGRES_PASSWORD="password" # Database password
POSTGRES_DB="lorcan" # Name of the database you created
test_database_name="lorcan_test" # Name of the test database
database_private_address="localhost" # Private address (default is 'localhost')
database_public_address="localhost" # Public address (default is 'localhost')
database_port=5432 # Database port (default is 5432)
```

Now, to apply migrations, run the following commands:

```bash
alembic upgrade head
```

```bash
alembic revision --autogenerate -m "setup the project"
```

```bash
alembic upgrade head
```

Congratulations! The project is successfully set up. To run the server, use the following command:

```bash
uvicorn app.main:app --reload
```

now open your browser and type url http://127.0.0.1:8000/docs#/

![Alt Text](./app/assets/screenshot.png)

