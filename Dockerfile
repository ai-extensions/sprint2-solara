FROM python:3.10
RUN pip3 install \
    jhsingle-native-proxy>=0.0.9 \
    shapely \
    leafmap \
    geopandas \
    loguru \
    solara \
    ipysheet

# create a user, since we don't want to run as root
RUN useradd -m worker
ENV HOME=/home/worker
WORKDIR $HOME
USER worker

COPY --chown=worker:worker entrypoint.sh /home/worker
RUN chmod +x /home/worker/entrypoint.sh
COPY --chown=worker:worker app.py /home/worker

EXPOSE 8888

ENTRYPOINT ["/home/worker/entrypoint.sh"]