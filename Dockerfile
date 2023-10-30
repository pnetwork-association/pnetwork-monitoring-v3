FROM python:3.11 AS pipenv_stage
RUN mkdir /pnetwork-monitoring
COPY Pipfile.lock /pnetwork-monitoring
WORKDIR /pnetwork-monitoring
RUN pip install pipenv && \
  pipenv install --ignore-pipfile

FROM pipenv_stage
COPY scripts/ /pnetwork-monitoring/scripts
COPY abi/ /pnetwork-monitoring/abi
COPY checks_mapping.py config.py constants.py \
  main.py Pipfile Pipfile.lock /pnetwork-monitoring/
ENTRYPOINT [ "pipenv", "run", "python", "main.py" ]
