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
item_link = "item_link"
collection_id = "collection_id"
stac_file_name = "stac_file_name"
item_id = "item_id"

stac_variables = {
    annotation_filename: solara.reactive("data.geojson"),
    asset_link: solara.reactive(""),
    asset_title: solara.reactive(""),
    item_label_description: solara.reactive(""),
    item_label_task_type: solara.reactive(""),
    item_link: solara.reactive(""),
    collection_id: solara.reactive(""),
    stac_file_name: solara.reactive(""),
    item_id: solara.reactive(""),
}

# Behavior variables
continuous_update = solara.reactive(True)
show_instruction_message = solara.reactive(True)


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
        stac_item_link,
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
        stac_item_link: STAC asset link of EO data used to create annotation

    """
    bbox = get_annotation_bbox(filename)
    file_size = os.stat(filename).st_size
    label_properties = create_label_properties(
        filename=filename, description=label_description, type_of_task=label_task_type
    )
    item = {
        "stac_version": "1.0.0",
        "stac_extensions": ["https://stac-extensions.github.io/label/v1.0.1/schema.json"],
        "type": "Feature",
        "id": stac_id,
        "bbox": bbox,
        "geometry": {"type": "Polygon", "coordinates": bbox},
        "properties": label_properties,
        "links": [{"rel": "source", "href": stac_item_link}],
        "assets": {
            "labels": {
                "href": stac_asset,
                "title": stac_title,
                "type": "application/geo+json",
                "file:size": file_size,
                "roles": [],
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
def stac_item_creation_component():
    """
    Solara component responsible for creation of STAC item based on annotation geojson file
    """
    with solara.Head():
        solara.Title("Annotation Tool")

    with solara.AppBarTitle():
        solara.Text("Annotation Tool")

    with solara.Sidebar():
        solara.Switch(label="See Instructions", value=show_instruction_message)
        if show_instruction_message.value:
            with solara.Card("STAC Item Creation", margin=0, elevation=0, style="max-width:600px"):
                solara.Markdown(
                    r"""
                _Before creating a STAC item, a geojson file containing annotations needs to be created._

                _This will only create a partial STAC item, containing the bounding box information._

                _In order to create this file, follow this Leafmap example :
                [Create Vector with Leafmap](https://leafmap.org/notebooks/45_create_vector/)_

                _The bounding box information will be calculated automatically._

                _Make sure that your file names match between the created geojson file using Leafmap
                and the STAC item file name below, and don't change the folder where the file is saved._

                _For more information on the STAC specification, see the
                [STAC specification](https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md)._
                """
                )
        solara.Markdown(
            r"""
        ### Arguments
        _Required elements marked with an (*)_
        """
        )
        with solara.Row():
            solara.InputText(
                "* Geojson annotation file name",
                value=stac_variables[annotation_filename],
                continuous_update=continuous_update.value,
            )

        with solara.Row():
            path = stac_variables[annotation_filename].value
            if not os.path.isfile(path):
                solara.Warning(f"No annotation file named [{path}] was not found.")

        with solara.Row():
            solara.InputText(
                "* STAC Item ID (stac_item.id)",
                value=stac_variables[item_id],
                continuous_update=continuous_update.value,
            )
        with solara.Row():
            if not stac_variables[item_id].value:
                solara.Warning(f"STAC Item ID is required")

        with solara.Row():
            path = f"./{stac_variables[item_id].value}_stac_item.json"
            if os.path.isfile(path):
                solara.Warning(f"STAC item file already exist with that ID")

        with solara.Row():
            solara.InputText(
                "* STAC Item Asset Label Title (stac_item.assets.labels.title)",
                value=stac_variables[asset_title],
                continuous_update=continuous_update.value,
            )
        with solara.Row():
            if not stac_variables[asset_title].value:
                solara.Warning(f"STAC Item Asset Label Title is required")

        with solara.Row():
            solara.InputText(
                "STAC Item Property Label Description (stac_item.properties.label:description)",
                value=stac_variables[item_label_description],
                continuous_update=continuous_update.value,
            )
        with solara.Row():
            solara.InputText(
                "STAC Item Property Label Task Type (stac_item.properties.label:tasks)",
                value=stac_variables[item_label_task_type],
                continuous_update=continuous_update.value,
                message="Usually either classification or segmentation.",
            )
        with solara.Row():
            solara.InputText(
                "STAC Item Asset Label Link (stac_item.assets.labels.href)",
                value=stac_variables[asset_link],
                continuous_update=continuous_update.value,
            )

        with solara.Row():
            solara.InputText(
                "STAC Item collection (stac_item.collection)",
                value=stac_variables[collection_id],
                continuous_update=continuous_update.value,
            )
        with solara.Row():
            solara.InputText(
                "EO data source used to create labels (stac_item.links.source.href)",
                value=stac_variables[item_link],
                continuous_update=continuous_update.value,
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
                    stac_item_link=stac_variables[item_link].value,
                ),
                color="green",
            )


def map_component():
    """
    Solara component responsible for the Map instance
    Returns:

    """
    with solara.Column(align="stretch"):
        Map.element(  # type: ignore
            zoom=zoom.value, on_zoom=zoom.set, center=center.value, on_center=center.set, scroll_wheel_zoom=True
        )


@solara.component
def Page():
    stac_item_creation_component()
    map_component()
