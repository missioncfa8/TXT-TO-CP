# Use a Python 3.12.3 Alpine base image
FROM python:3.12-alpine3.20

# Set the working directory
WORKDIR /app

# Copy only requirements files first for better caching
COPY sainibots.txt ./

# Install necessary system dependencies
RUN apk add --no-cache \
    gcc \
    libffi-dev \
    musl-dev \
    ffmpeg \
    aria2 \
    make \
    g++ \
    cmake && \
    wget -q https://github.com/axiomatic-systems/Bento4/archive/v1.6.0-639.zip && \
    unzip v1.6.0-639.zip && \
    cd Bento4-1.6.0-639 && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j$(nproc) && \
    cp mp4decrypt /usr/local/bin/ &&\
    cd ../.. && \
    rm -rf Bento4-1.6.0-639 v1.6.0-639.zip

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir --upgrade -r sainibots.txt \
    && python3 -m pip install -U yt-dlp

# Copy all other files after dependencies are installed
COPY . .

# Set the command to run the application
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app & python3 main.py"]