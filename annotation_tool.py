import datetime
import json
import os

import fiona
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
stac_annotation_filename = solara.reactive("data.geojson")
stac_asset_link = solara.reactive("")
stac_asset_title = solara.reactive("")
stac_item_link = solara.reactive("")
stac_collection_id = solara.reactive("")
stac_file_name = solara.reactive("")
stac_item_id = solara.reactive("")

# Behavior variables
continuous_update = solara.reactive(True)
show_instruction_message = solara.reactive(True)


#
# Utility functions
#
def get_annotation_bbox(filename=stac_annotation_filename.value):
    """
    Create bounding box for a given annotation file

    Args:
        filename: File name of the geojson annotation file

    Returns: Bounding box in list form

    """
    annotations = fiona.open(filename)
    return list(annotations.bounds)


def create_stac_item(
    filename=stac_annotation_filename.value,
    stac_id=stac_item_id.value,
    stac_title=stac_asset_title.value,
    stac_asset=stac_asset_link.value,
    collection_id=stac_collection_id.value,
    item_link=stac_item_link.value,
):
    """
    Create a STAC item stub from a geojson annotation file, which
    can later be expanded.

    Args:
        filename: Geojson annotation file name/path
        stac_id: ID for new STAC item
        stac_asset: Link to the asset, which is the hosted Geojson annotation file
        stac_title: Title for the Geojson annotation file asset
        collection_id: STAC collection ID, if applicable
        item_link: STAC asset link of EO data used to create annotation

    """
    bbox = get_annotation_bbox(filename)
    file_size = os.stat(filename).st_size
    item = {
        "stac_version": "1.0.0",
        "type": "Feature",
        "id": stac_id,
        "bbox": bbox,
        "geometry": {"type": "Polygon", "coordinates": bbox},
        "properties": {"created": datetime.datetime.now().isoformat()},
        "links": [{"rel": "derived_from", "href": item_link}],
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
        item["collection"] = stac_collection_id.value

    with open(f"./{stac_item_id.value}_stac_item.json", "w") as stac_file:
        json.dump(item, stac_file, indent=4)


def clear_all():
    # Function to clear all text inputs from STAC creation form
    stac_annotation_filename.set("data.geojson")
    stac_item_link.set("")
    stac_collection_id.set("")
    stac_file_name.set("")
    stac_item_id.set("")


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
                value=stac_annotation_filename,
                continuous_update=continuous_update.value,
            )

        with solara.Row():
            path = stac_annotation_filename.value
            if not os.path.isfile(path):
                solara.Warning(f"No annotation file named [{path}] was not found.")

        with solara.Row():
            solara.InputText(
                "* STAC Item ID (stac_item.id)", value=stac_item_id, continuous_update=continuous_update.value
            )
        with solara.Row():
            path = f"./{stac_item_id.value}_stac_item.json"
            if os.path.isfile(path):
                solara.Warning(f"STAC item file already exist with that ID")

        with solara.Row():
            solara.InputText(
                "STAC Item Asset Label Title (stac_item.assets.labels.title)",
                value=stac_asset_title,
                continuous_update=continuous_update.value,
            )
        with solara.Row():
            solara.InputText(
                "STAC Item Asset Label Link (stac_item.assets.labels.href)",
                value=stac_asset_link,
                continuous_update=continuous_update.value,
            )

        with solara.Row():
            solara.InputText(
                "STAC Item collection (stac_item.collection)",
                value=stac_collection_id,
                continuous_update=continuous_update.value,
            )
        with solara.Row():
            solara.InputText(
                "EO data derived from link (stac_item.links.derived_from.href)",
                value=stac_item_link,
                continuous_update=continuous_update.value,
            )

        with solara.Row():
            solara.Button("Clear", on_click=clear_all)
            solara.Button("Create", on_click=create_stac_item, color="green")


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
