FROM python:alpine
WORKDIR /usr/src/app
RUN pip install --no-cache-dir spotipy
COPY producer.py .
ENTRYPOINT [ "/bin/sh" ]
# ENTRYPOINT ["python3", "producer.py"]
