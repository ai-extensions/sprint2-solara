# Simple Solara app

This example app has been built from the https://github.com/ai-extensions/sprint2-streamlit.git app.

This is still in progress and implemented as an example of how to use Leafmap in a Solara application
as an annotation app example.

## Known issues

[Ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) currently has a bug (possibly through Ipywidgets) 
that impacts the [Draw functionality](https://github.com/jupyter-widgets/ipyleaflet/issues/1119), hence limiting our 
use of [Leafmap](https://github.com/opengeos/leafmap) as an annotation tool. There is an open 
[Pull Request](https://github.com/jupyter-widgets/ipyleaflet/pull/1133) about it, but it has yet to be finalized.

While we can pin Ipyleaflet and Ipywidgets to previous versions and make the Solara app work inside a Notebook 
(see [annotation_tool_example.ipynb](annotation_tool_example.ipynb)), the bug is still in effect when we launch 
the Solara components as a standalone application. This behavior has been tested using both Solara (`solara run`) and 
packaging it in a `Flask` application.

The proposed solution, for the time being, is to simply integrate the annotation tool inside the 
[s2-labellingEOdata notebook](https://github.com/ai-extensions/notebooks/blob/main/scenario-2/s2-labellingEOdata.ipynb).

## Execution steps using Visual Studio Code and Dev Containers

* Start Docker Desktop
* Start VS Code 
* Command Palette > Dev Containers: Clone Repository in named Container Volume... (note: you must have the Dev Containers extension installed)
* Paste the repository link https://github.com/ai-extensions/sprint2-solara.git
* Create a new Volume (type the name or use default name)
* Name folder (type the name or use default `sprint2-solara`)
* The creation and set-up of the dev container will start. When it finishes, open a Terminal and run:
    ```
    solara run annotation_tool.py
    ```
* you can open the Solara app by clicking the "Open in Browser" button in the pop-up window.

## Execution steps with local container

### Build local container
```
docker build -t solara-hw .
```
or
```
make docker-build
```

### Run container
```
docker run -p 8888:8888 --rm -it solara-hw 
``` 
or
```
make docker-run
```

Open the app on a web browser on local port `http://localhost:8888/`

### Run application locally

```
solara run annotation_tool.py 
``` 
or
```
make solara-run
```