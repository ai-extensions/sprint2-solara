import leafmap
import solara
from leafmap.toolbar import change_basemap

# from .custom_annotation_toolbar import edit_draw_gui2

zoom = solara.reactive(4)
center = solara.reactive((20, 0))


class Map(leafmap.Map):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add and/or modify components to define default toolbars and elements of the map
        self.layout.height = "800px"
        leafmap.toolbar.layer_manager_gui(self, position="bottomleft")
        leafmap.toolbar.stac_gui(self)
        leafmap.toolbar.edit_draw_gui(self)
        # edit_draw_gui2(self)


@solara.component
def Page():
    with solara.Head():
        solara.Title("Annotation Tool")

    with solara.AppBarTitle():
        solara.Text("Annotation Tool")

    with solara.Column(align="stretch"):
        Map.element(  # type: ignore
            zoom=zoom.value,
            on_zoom=zoom.set,
            center=center.value,
            on_center=center.set,
            scroll_wheel_zoom=True,
            toolbar_control=True,
            data_control=True,
        )
