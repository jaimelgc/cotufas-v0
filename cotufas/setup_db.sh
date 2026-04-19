#!/bin/bash

read -p "Enter name: " DB_USER
read -p "Enter password: " DB_PASSWORD
read -p "Enter database: " DB_NAME

echo "Creating PostgreSQL user..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

echo "Creating database..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "Running Django migrations..."
python manage.py migrate

echo "Setup complete!"