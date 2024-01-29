import datetime
import json
import os

import fiona
import geopandas
import ipywidgets
import leafmap
import solara
from leafmap import toolbar

#
# Application variables
#
# Map variables
center = solara.reactive((20, 0))
zoom = solara.reactive(4)

# STAC creation variables
annotation_filename = "annotation_filename"
asset_link = "asset_link "
asset_title = "asset_title"
item_label_description = "label_description"
item_label_task_type = "item_label_task_type"
item_source_link = "item_source_link"
collection_id = "collection_id"
stac_file_name = "stac_file_name"
item_id = "item_id"

stac_variables = {
    annotation_filename: solara.reactive("data.geojson"),
    asset_link: solara.reactive(""),
    asset_title: solara.reactive(""),
    item_label_description: solara.reactive(""),
    item_label_task_type: solara.reactive(""),
    item_source_link: solara.reactive(""),
    collection_id: solara.reactive(""),
    stac_file_name: solara.reactive(""),
    item_id: solara.reactive(""),
}

# Behavior variables
continuous_update = solara.reactive(True)
show_annotation_message = solara.reactive(True)
show_stac_item_message = solara.reactive(True)


#
# Utility functions
#
def get_annotation_bbox(filename):
    """
    Create bounding box for a given annotation file

    Args:
        filename: File name of the geojson annotation file

    Returns: Bounding box in list form

    """
    annotations = fiona.open(filename)
    return list(annotations.bounds)


def create_label_classes(properties):
    classes = []
    for p in properties:
        unique_values = properties[p].unique()
        unique_values.sort()
        values = unique_values.tolist()
        classes.append({"name": p, "classes": values})
    return classes


def create_label_overviews(properties):
    overviews = []
    for p in properties:
        unique_values = properties[p].unique()
        unique_values.sort()
        counts = []
        class_value_counts = properties[p].value_counts().to_dict()
        class_count_list = [{"name": k, "count": v} for k, v in class_value_counts.items()]
        counts.extend(class_count_list)
        overviews.append({"property_key": p, "counts": counts})
    return overviews


def create_label_properties(
        filename,
        description,
        type_of_task,
):
    if isinstance(type_of_task, str):
        type_of_task = [type_of_task]
    gdf = geopandas.read_file(filename)
    filtered_gdf = gdf.loc[:, ~gdf.columns.isin(["id", "geometry"])]
    properties = filtered_gdf.columns.tolist()

    label_classes = create_label_classes(filtered_gdf)
    label_overview = create_label_overviews(filtered_gdf)

    label_properties_json = {
        "datatime": datetime.datetime.now().isoformat(),
        "label:type": "vector",
        "label:description": description,
        "label:properties": properties,
        "label:classes": label_classes,
        "label:tasks": type_of_task,
        "label:methods": ["manual"],
        "version": "1",
        "label:overviews": label_overview,
        "label:assets": ["labels"]
    }
    return label_properties_json


def create_stac_item(
        filename,
        stac_id,
        stac_title,
        stac_asset,
        stac_collection_id,
        label_description,
        label_task_type,
        stac_item_source_link,
):
    """
    Create a STAC item stub from a geojson annotation file, which
    can later be expanded.

    Args:
        filename: Geojson annotation file name/path
        stac_id: ID for new STAC item
        stac_asset: Link to the asset, which is the hosted Geojson annotation file
        stac_title: Title for the Geojson annotation file asset
        stac_collection_id: STAC collection ID, if applicable
        label_description: Description of the labels
        label_task_type: Type of task for which the labels will be used
        stac_item_source_link: STAC asset link of EO data used to create annotation

    """
    bbox = get_annotation_bbox(filename)
    file_size = os.stat(filename).st_size
    label_properties = create_label_properties(
        filename=filename, description=label_description, type_of_task=label_task_type
    )

    if stac_asset.strip() == "":
        stac_asset = filename

    item = {
        "stac_version": "1.0.0",
        "stac_extensions": ["https://stac-extensions.github.io/label/v1.0.1/schema.json"],
        "type": "Feature",
        "id": stac_id,
        "bbox": bbox,
        "geometry": {"type": "Polygon", "coordinates": bbox},
        "properties": label_properties,
        "links": [{"rel": "source", "href": stac_item_source_link}],
        "assets": {
            "labels": {
                "href": stac_asset,
                "title": stac_title,
                "type": "application/geo+json",
                "file:size": file_size,
                "roles": ["data"],
            }
        },
    }
    if collection_id:
        item["collection"] = stac_collection_id

    with open(f"./{stac_id}_stac_item.geojson", "w") as stac_file:
        json.dump(item, stac_file, indent=4)


def clear_all():
    # Function to clear all text inputs from STAC creation form
    for _, variable in stac_variables.items():
        variable.set("")
    stac_variables[annotation_filename].set("data.geojson")


#
# Custom Map class
#
class Map(leafmap.Map):
    """
    Map class necessary to set some default values for toolbars and properties.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add and/or modify components to define default toolbars and elements of the map
        self.layout.height = "700px"
        leafmap.toolbar.layer_manager_gui(self, position="bottomleft")
        leafmap.toolbar.edit_draw_gui(self)
        # edit_draw_gui_alternative(self)

        # Custom widgets to simplify saving annotations
        annotations_name = ipywidgets.Text(
            value="data.geojson", description="Filename", description_tooltip="File name for annotations"
        )
        button = ipywidgets.Button(description=f"Save annotations")

        def save_annotations(btn):
            self.save_draw_features(annotations_name.value)

        button.on_click(save_annotations)
        side_by_side = ipywidgets.HBox([annotations_name, button])
        self.add_widget(side_by_side)


#
# Solara components
#
@solara.component
def stac_item_creation_component():
    """
    Solara component responsible for creation of STAC item based on annotation geojson file
    """

    with solara.Card():
        solara.Switch(label="See Instructions", value=show_stac_item_message)
        if show_stac_item_message.value:
            with solara.Card("STAC Item Creation", margin=0, elevation=0):
                solara.Markdown(
                    r"""
                _This will only create a partial STAC item that can also be completed in later steps_

                _The bounding box information will be calculated automatically._

                _Many properties of the Label Extension are also automatically calculated, like the statistics about
                the labels._

                _Make sure that your file names match between the created geojson file using Leafmap
                and the STAC item input file name below, and don't change the folder where the file is saved._

                _For more information on the `STAC specification`, see the
                <a href="https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md" target="_blank">STAC specification</a>._

                _For more information about the `Label Extension`, see 
                <a href="https://github.com/stac-extensions/label" target="_blank">Label Extension Specification</a>._


                _For implementation examples of the `Label Extension`, see 
                <a href="https://github.com/stac-extensions/label/tree/main/examples" target="_blank">Label Extension Examples</a>._
                """
                )

        with solara.Column():
            solara.Markdown(
                r"""
                <br>
                ## Required Arguments
                """
            )

            solara.InputText(
                "The filepath to Geojson annotation file (Path relative to notebook. Validation on change only)",
                value=stac_variables[annotation_filename],
                continuous_update=continuous_update.value,
            )

            path = stac_variables[annotation_filename].value
            if not os.path.isfile(path):
                solara.Warning(f"No annotation file named [{path}] was not found.")

            solara.InputText(
                "The STAC Item ID for the annotations (stac_item.id)",
                value=stac_variables[item_id],
                continuous_update=continuous_update.value,
            )

            if not stac_variables[item_id].value:
                solara.Warning(f"STAC Item ID is required")

            path = f"./{stac_variables[item_id].value}_stac_item.json"
            if os.path.isfile(path):
                solara.Warning(f"STAC item file already exist with that ID")

            solara.InputText(
                "The title for the annotations of the STAC Item Assets (stac_item.assets.labels.title)",
                value=stac_variables[asset_title],
                continuous_update=continuous_update.value,
            )

            if not stac_variables[asset_title].value:
                solara.Warning(f"STAC Item Asset Label Title is required")

            solara.Markdown(
                r"""
                <br>
                ## STAC Item Label Properties
                """
            )

            solara.InputText(
                "Label Description (stac_item.properties.label:description)",
                value=stac_variables[item_label_description],
                continuous_update=continuous_update.value,
            )

            solara.InputText(
                "Task types the annotations will be used for (stac_item.properties.label:tasks)",
                value=stac_variables[item_label_task_type],
                continuous_update=continuous_update.value,
                message="Usually either classification or segmentation.",
            )

            solara.Markdown(
                r"""
                <br>
                ## STAC Item Sources, Links and Other Properties
                """
            )

            solara.InputText(
                "The collection the STAC Item belongs to (stac_item.collection)",
                value=stac_variables[collection_id],
                continuous_update=continuous_update.value,
            )

            solara.InputText(
                "EO data source used to create labels (stac_item.links.source.href)",
                value=stac_variables[item_source_link],
                continuous_update=continuous_update.value,
            )

            solara.InputText(
                "Link to the geojson containing the annotations (stac_item.assets.labels.href)",
                value=stac_variables[asset_link],
                continuous_update=continuous_update.value,
                message="If left empty, will default to Geojson annotations file name input above"
            )

            with solara.Row():
                solara.Button("Clear", on_click=clear_all)
                solara.Button(
                    "Create",
                    on_click=lambda: create_stac_item(
                        filename=stac_variables[annotation_filename].value,
                        stac_id=stac_variables[item_id].value,
                        stac_title=stac_variables[asset_title].value,
                        stac_asset=stac_variables[asset_link].value,
                        stac_collection_id=stac_variables[collection_id].value,
                        label_description=stac_variables[item_label_description].value,
                        label_task_type=stac_variables[item_label_task_type].value,
                        stac_item_source_link=stac_variables[item_source_link].value,
                    ),
                    color="green",
                )

            solara.Markdown(
                r"""
                _Clicking the `CREATE` button will create a geojson file named `<stac_id>_stac_item.geojson` in the 
                notebook's current directory._
                """
            )


@solara.component
def map_component():
    """
    Solara component responsible for the Map instance
    Returns:

    """
    solara.Switch(label="See Instructions", value=show_annotation_message)
    if show_annotation_message.value:
        with solara.Card("Annotation Creation", margin=0, elevation=0):
            solara.Markdown(
                r"""
                _The `map` below is a customized <a href="https://leafmap.org/" target="_blank">Leafmap</a> 
                map instance, itself using <a href="https://ipyleaflet.readthedocs.io/en/latest/" target="_blank">Ipyleaflet</a>_

                _In order to create you annotations, follow this Leafmap example about vector creation : 
                <a href="https://leafmap.org/notebooks/45_create_vector/" target="_blank">Create Vector with Leafmap</a>_

                _For convenience, a `Save Annotations` toolbar (lower right corner) has been added to the 
                directly to map which simplifies the process to save the annotations to file._
            """
            )

    with solara.Column(align="stretch"):
        Map.element(  # type: ignore
            zoom=zoom.value, on_zoom=zoom.set, center=center.value, on_center=center.set, scroll_wheel_zoom=True
        )

routes = [
    solara.Route(path="/", component=map_component, label="Annotation Tool"),
    solara.Route(path="stac", component=stac_item_creation_component, label="STAC Item Creation"),
]
