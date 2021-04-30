FROM alpine

RUN apk add --no-cache python3 py3-pip postgresql \
    postgresql-dev gcc python3-dev musl-dev

RUN mkdir /_
COPY ../setup.py /_/setup.py
COPY ../README.md /_/README.md
COPY ../django_client_framework /_/django_client_framework
RUN pip3 install /_
COPY . /_

ENV PYTHONPATH /_

WORKDIR /_/unit-tests
ENTRYPOINT [ "./manage.py" ]
