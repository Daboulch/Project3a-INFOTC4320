#Use an official python image as the base image
FROM python:3.11-slim

#Set the working directory in the container to /app
WORKDIR /app

#Copy the contents of the current directory in the container /app directory
COPY . /app

#Upgrade pip and install the packages from requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]