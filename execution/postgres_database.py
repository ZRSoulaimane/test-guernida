import psycopg2
try:
    connection = psycopg2.connect(
            host='host.docker.internal',
            port='5432',
            user='postgres',
            password='salma',
            database='guernida'
        )
    cur = connection.cursor()

    cursor = connection.cursor()

    create_table_query = '''
    CREATE TABLE IF NOT EXISTS your_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        age INTEGER
    ) '''
    cursor.execute(create_table_query)
    connection.commit()
    print("Table created successfully.")

except (Exception, psycopg2.Error) as error:
    print("Error creating table:", error)