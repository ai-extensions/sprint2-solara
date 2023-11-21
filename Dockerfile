FROM python:3.10-slim
# Currently an issue with ipyleaflet/ipywidgets with the DrawControls, requiring fixed dependencies
# See : https://github.com/jupyter-widgets/ipyleaflet/issues/1119

# create a user, since we don't want to run as root
RUN useradd -m worker
ENV HOME=/home/worker
ENV PATH=${HOME}/.local/bin:$PATH
WORKDIR ${HOME}
USER worker

# Install requirements
COPY --chown=worker:worker requirements.txt /home/worker
RUN pip3 install -r requirements.txt

# Copy module and entrypoint
COPY --chown=worker:worker entrypoint.sh /home/worker
RUN chmod +x /home/worker/entrypoint.sh
COPY --chown=worker:worker annotation_tool.py /home/worker

EXPOSE 8888

ENTRYPOINT ["/home/worker/entrypoint.sh"]