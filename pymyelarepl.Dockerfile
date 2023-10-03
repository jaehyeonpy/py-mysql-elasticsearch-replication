ARG BASE_IMAGE
FROM ${BASE_IMAGE}

COPY pymyelarepl pymyelarepl/pymyelarepl
COPY example pymyelarepl/example
COPY test pymyelarepl/test
COPY setup.py pymyelarepl/setup.py
RUN cd pymyelarepl && pip install .