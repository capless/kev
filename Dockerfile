FROM capless/capless-docker:2
COPY . /code
RUN poetry install