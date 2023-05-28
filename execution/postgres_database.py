import psycopg2
print("start")
try:
    connection = psycopg2.connect(
            host='host.docker.internal',
            port='5432',
            user='postgres',
            password='salma',
            database='guernida'
        )
    print("1")
    cur = connection.cursor()
    print("2")


    cursor = connection.cursor()

    create_table_query = '''
    CREATE TABLE IF NOT EXISTS your_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        age INTEGER
    )
'''
    cursor.execute(create_table_query)
    connection.commit()
    print("Table created successfully.")

except (Exception, psycopg2.Error) as error:
    print("Error creating table:", error)
