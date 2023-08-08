FROM alpine

# Install MySQL client, python3, and required libraries
RUN apk add --no-cache mysql-client python3 py3-pip
RUN pip3 install numpy mysql-connector-python

# Set a working directory
WORKDIR /app

# Copy our Python script to the container
COPY populate_db_mysql.py .

CMD ["python3", "populate_db_mysql.py"]
