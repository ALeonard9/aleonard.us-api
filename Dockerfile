FROM python:3.12.3-alpine
# EXPOSE 5000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
CMD ["/bin/ash", "docker-entrypoint.sh"]
# CMD ["flask", "run", "--host=0.0.0.0"]