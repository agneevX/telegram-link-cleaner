FROM python:3.9

ENV VIRTUAL_ENV=/app
ENV PATH="$PATH:$VIRTUAL_ENV/bin"

COPY . $VIRTUAL_ENV

RUN apt-get update \
        && apt-get -yq install python3-dev git

RUN python3 -m venv $VIRTUAL_ENV

RUN git clone https://github.com/AmanoTeam/Unalix \
        && cd Unalix \
        && python external/update_rules_file.py \
        && pip install .

RUN pip install -r /app/requirements.txt

CMD ["python", "/app/main_file.py"]
