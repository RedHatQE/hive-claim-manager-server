FROM quay.io/redhat_msi/qe-tools-base-image:latest

EXPOSE 5000
RUN apt-get update \
  && apt-get install -y redis --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV APP_DIR=/hive-claim-manager-server
ENV POETRY_HOME=$APP_DIR
ENV PATH="$APP_DIR/bin:$PATH"

COPY pyproject.toml poetry.lock README.md entrypoint.sh $APP_DIR/
COPY api $APP_DIR/api/

WORKDIR $APP_DIR

RUN python3 -m pip install --no-cache-dir --upgrade pip --upgrade \
  && python3 -m pip install --no-cache-dir poetry \
  && poetry config cache-dir $APP_DIR \
  && poetry config virtualenvs.in-project true \
  && poetry config installer.max-workers 10 \
  && poetry install

HEALTHCHECK CMD curl --fail http://127.0.0.1:5000/healthcheck || exit 1
ENTRYPOINT ["./entrypoint.sh"]
