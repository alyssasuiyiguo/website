# Use the official Python 3.12 image as a base
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code into the container
# This copies everything from your local directory into /app in the container
COPY . .

# Cloud Run Jobs do not need to listen on a port or expose one.
# They simply run the specified command to completion.
# So, no ENV PORT or EXPOSE needed.

# Define the ENTRYPOINT as the Python interpreter
# This ensures 'python' is always the executable that runs so that container arguments can be appended correctly on execution
ENTRYPOINT ["python"]

# Define the command to run your application
# This is the command that gets executed when the job starts
CMD ["add_metadata.py", "--generateAltSentences", "--useGCS", "--useBigQuery", "--maxStatVars=10000"]