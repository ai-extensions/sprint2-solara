# Simple Solara app

This example app has been built from the https://github.com/ai-extensions/sprint2-streamlit.git app.

This is still in progress and implemented as an example of how to use Leafmap in a Solara application
as an annotation app example.

## Execution steps using Visual Studio Code and Dev Containers

* Start Docker Desktop
* Start VS Code 
* Command Palette > Dev Containers: Clone Repository in named Container Volume... (note: you must have the Dev Containers extension installed)
* Paste the repository link https://github.com/ai-extensions/sprint2-solara.git
* Create a new Volume (type the name or use default name)
* Name folder (type the name or use default `sprint2-solara`)
* The creation and set-up of the dev container will start. When it finishes, open a Terminal and run:
    ```
    solara run app.py
    ```
* you can open the Solara app by clicking the "Open in Browser" button in the pop-up window.

## Execution steps with local container

Build local container
```
docker build -t solara-hw .
```

Run container
```
docker run -p 8888:8888 --rm -it solara-hw 
``` 

Open the app on a web browser on local port `http://localhost:8888/`