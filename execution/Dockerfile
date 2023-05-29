# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /opt

# Install system-level dependencies
RUN apt-get update && apt-get install -y wget unzip curl gnupg2

# install google chrome
RUN apt-get install -y wget curl
RUN wget -vO linux_signing_key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub
RUN apt-key add linux_signing_key.pub
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# Install ChromeDriver
ARG CHROME_DRIVER_VERSION=113.0.5672.24
RUN wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" -O chromedriver.zip \
    && unzip chromedriver.zip \
    && rm chromedriver.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver

# Copy the Python requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY . .

# Set the command to run your Python script
CMD ["python3", "scheduler.py"]