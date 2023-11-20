"""
Work in progress

This is a copy of the vector editing toolbar from the Leafmap library.

The purpose is to refactor it to make it easier to save and download
created annotation files
"""

import os

import ipyevents
import ipyleaflet
import ipysheet
import ipywidgets as widgets
import pandas as pd
from ipyfilechooser import FileChooser
from IPython.display import display


def edit_draw_gui_alternative(m):
    """Generates a tool GUI for editing vector data attribute table.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}
    m.edit_mode = True

    n_props = len(m.get_draw_props())
    if n_props == 0:
        n_props = 1

    sheet = ipysheet.from_dataframe(m.get_draw_props(n_props, return_df=True))
    m.edit_sheet = sheet

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))
    m.edit_output = output

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Edit attribute table",
        icon="pencil-square-o",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    save_button = widgets.ToggleButton(
        value=False,
        tooltip="Save to file",
        icon="floppy-o",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    int_slider = widgets.IntSlider(
        min=n_props,
        max=n_props + 10,
        description="Attributes:",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="135px", padding=padding),
        style=style,
    )

    int_slider_label = widgets.Label()
    widgets.jslink((int_slider, "value"), (int_slider_label, "value"))

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "60px"

    with output:
        output.clear_output()
        display(m.edit_sheet)

    def int_slider_changed(change):
        if change["new"]:
            m.edit_sheet.rows = int_slider.value
            m.num_attributes = int_slider.value
            with output:
                output.clear_output()
                m.edit_sheet = ipysheet.from_dataframe(
                    m.get_draw_props(n=int_slider.value, return_df=True)
                )
                display(m.edit_sheet)

    int_slider.observe(int_slider_changed, "value")
    m.num_attributes = int_slider.value

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [
        close_button,
        toolbar_button,
        save_button,
        int_slider,
        int_slider_label,
    ]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        output,
        buttons,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.edit_mode = False
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def chooser_callback(chooser):
        m.save_draw_features(chooser.selected, indent=None)
        if m.file_control in m.controls:
            m.remove_control(m.file_control)
        with output:
            print(f"Saved to {chooser.selected}")

    def save_btn_click(change):
        if change["new"]:
            save_button.value = False

            file_chooser = FileChooser(
                os.getcwd(),
                sandbox_path=m.sandbox_path,
                layout=widgets.Layout(width="454px"),
            )
            file_chooser.filter_pattern = ["*.shp", "*.geojson", "*.gpkg"]
            file_chooser.default_filename = "data.geojson"
            file_chooser.use_dir_icons = True
            file_chooser.register_callback(chooser_callback)

            file_control = ipyleaflet.WidgetControl(
                widget=file_chooser, position="topright"
            )
            m.add_control(file_control)
            m.file_control = file_control

    save_button.observe(save_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.clear_output()
                display(m.edit_sheet)
                if len(m.draw_control.data) == 0:
                    print("Please draw a feature first.")
                else:
                    m.update_draw_props(ipysheet.to_dataframe(m.edit_sheet))
        elif change["new"] == "Reset":
            m.edit_sheet = ipysheet.from_dataframe(
                m.get_draw_props(int_slider.value, return_df=True)
            )
            with output:
                output.clear_output()
                display(m.edit_sheet)
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.edit_mode = False
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget
