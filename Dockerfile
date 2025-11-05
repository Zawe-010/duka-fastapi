FROM python:3.11-slim

WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app folder
COPY ./app ./app

# Expose port
EXPOSE 80

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
