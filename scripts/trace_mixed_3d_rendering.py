import json
import os
import statistics
import sys
import time
import traceback

import qt
import slicer
import vtk


def print_line(message):
    print(message)
    sys.stdout.flush()


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def safe_mean(values):
    return statistics.mean(values) if values else 0.0


def safe_median(values):
    return statistics.median(values) if values else 0.0


def safe_stdev(values):
    return statistics.stdev(values) if len(values) > 1 else 0.0


def safe_call(obj, method_name, default=None):
    if not obj:
        return default
    method = getattr(obj, method_name, None)
    if not method:
        return default
    try:
        return method()
    except Exception:
        return default


def get_display_visibility_3d(display_node):
    if not display_node:
        return False
    getter = getattr(display_node, "GetVisibility3D", None)
    if getter:
        try:
            return bool(getter())
        except Exception:
            pass
    return bool(safe_call(display_node, "GetVisibility", 0))


def set_display_visibility_3d(display_node, visible):
    if not display_node:
        return
    setter = getattr(display_node, "SetVisibility3D", None)
    if setter:
        setter(int(visible))
        return
    fallback = getattr(display_node, "SetVisibility", None)
    if fallback:
        fallback(int(visible))


def dataset_stats(dataset):
    if not dataset:
        return {"points": 0, "cells": 0}
    stats = {
        "points": int(safe_call(dataset, "GetNumberOfPoints", 0) or 0),
        "cells": int(safe_call(dataset, "GetNumberOfCells", 0) or 0),
    }
    if dataset.IsA("vtkPolyData"):
        stats["polys"] = int(safe_call(dataset, "GetNumberOfPolys", 0) or 0)
        stats["lines"] = int(safe_call(dataset, "GetNumberOfLines", 0) or 0)
        stats["strips"] = int(safe_call(dataset, "GetNumberOfStrips", 0) or 0)
    return stats


def visibility_label(enabled):
    return "visible" if enabled else "hidden"


class MixedRenderTracer:
    def __init__(self):
        self.scene_path = os.environ.get("AIG_RENDER_TRACE_SCENE_PATH", "").strip()
        self.report_path = os.environ.get("AIG_RENDER_TRACE_REPORT_PATH", "").strip()
        self.json_path = os.environ.get("AIG_RENDER_TRACE_JSON_PATH", "").strip()
        self.view_index = env_int("AIG_RENDER_TRACE_VIEW_INDEX", 0)
        self.warmup_frames = max(1, env_int("AIG_RENDER_TRACE_WARMUP_FRAMES", 5))
        self.measured_frames = max(1, env_int("AIG_RENDER_TRACE_MEASURED_FRAMES", 20))
        self.synthetic_scene = env_bool("AIG_RENDER_TRACE_SYNTHETIC_SCENE", False)
        self.exit_code = 0
        self.internal_items = {"models": [], "volumes": []}
        self.report = {
            "status": "starting",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scene_path": self.scene_path or None,
            "synthetic_scene": self.synthetic_scene,
            "config": {
                "view_index": self.view_index,
                "warmup_frames": self.warmup_frames,
                "measured_frames": self.measured_frames,
            },
        }

    def process_events(self):
        qt.QApplication.processEvents()

    def ensure_layout_ready(self):
        layout_manager = slicer.app.layoutManager()
        if not layout_manager:
            raise RuntimeError("Layout manager is unavailable")
        three_d_widget = layout_manager.threeDWidget(self.view_index)
        if not three_d_widget:
            raise RuntimeError(f"3D widget index {self.view_index} is unavailable")
        return layout_manager, three_d_widget

    def prepare_scene(self):
        layout_manager, _ = self.ensure_layout_ready()
        layout_manager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
        self.process_events()

        if self.scene_path:
            print_line(f"Loading scene: {self.scene_path}")
            if not slicer.util.loadScene(self.scene_path):
                raise RuntimeError(f"Failed to load scene: {self.scene_path}")
        elif self.synthetic_scene:
            print_line("Creating synthetic trace scene")
            self.create_synthetic_scene()
        else:
            print_line("Using current scene without loading additional data")

        self.process_events()

    def create_synthetic_scene(self):
        slicer.mrmlScene.Clear(0)
        self.process_events()

        rt_source = vtk.vtkRTAnalyticSource()
        rt_source.SetWholeExtent(-72, 72, -72, 72, -48, 48)
        rt_source.Update()

        volume_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "SyntheticTraceVolume")
        volume_node.SetAndObserveImageData(rt_source.GetOutput())
        volume_node.SetSpacing(0.8, 0.8, 1.2)
        volume_node.CreateDefaultDisplayNodes()

        volume_rendering_logic = slicer.modules.volumerendering.logic()
        volume_display_node = volume_rendering_logic.CreateDefaultVolumeRenderingNodes(volume_node)
        preset = volume_rendering_logic.GetPresetByName("CT-Chest-Contrast-Enhanced")
        if preset:
            volume_display_node.GetVolumePropertyNode().Copy(preset)
        volume_display_node.SetVisibility(True)

        models_logic = slicer.modules.models.logic()

        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(0.0, 0.0, 0.0)
        sphere.SetRadius(48.0)
        sphere.SetThetaResolution(180)
        sphere.SetPhiResolution(180)
        sphere.Update()
        sphere_model = models_logic.AddModel(sphere.GetOutputPort())
        sphere_model.SetName("SyntheticSphere")
        sphere_model.GetDisplayNode().SetColor(0.85, 0.2, 0.2)
        sphere_model.GetDisplayNode().SetOpacity(0.85)

        cylinder = vtk.vtkCylinderSource()
        cylinder.SetCenter(70.0, 0.0, 0.0)
        cylinder.SetRadius(14.0)
        cylinder.SetHeight(120.0)
        cylinder.SetResolution(220)
        cylinder.CappingOn()
        cylinder.Update()
        cylinder_model = models_logic.AddModel(cylinder.GetOutputPort())
        cylinder_model.SetName("SyntheticCylinder")
        cylinder_model.GetDisplayNode().SetColor(0.2, 0.8, 0.25)
        cylinder_model.GetDisplayNode().SetOpacity(1.0)

        cone = vtk.vtkConeSource()
        cone.SetCenter(-76.0, -10.0, 0.0)
        cone.SetRadius(20.0)
        cone.SetHeight(110.0)
        cone.SetResolution(240)
        cone.Update()
        cone_model = models_logic.AddModel(cone.GetOutputPort())
        cone_model.SetName("SyntheticCone")
        cone_model.GetDisplayNode().SetColor(0.15, 0.35, 0.95)
        cone_model.GetDisplayNode().SetOpacity(0.7)

        self.report["scene_origin"] = "synthetic"

    def get_view_bundle(self):
        _, three_d_widget = self.ensure_layout_ready()
        view = three_d_widget.threeDView()
        view_node = three_d_widget.mrmlViewNode()
        render_window = view.renderWindow()
        renderers = render_window.GetRenderers()
        renderer = renderers.GetFirstRenderer() if renderers else None
        if not renderer:
            raise RuntimeError("No renderer available in target 3D view")
        model_displayable_manager = view.displayableManagerByClassName("vtkMRMLModelDisplayableManager")
        volume_displayable_manager = view.displayableManagerByClassName("vtkMRMLVolumeRenderingDisplayableManager")
        renderer.ResetCamera()
        render_window.Render()
        self.process_events()
        return {
            "widget": three_d_widget,
            "view": view,
            "view_node": view_node,
            "render_window": render_window,
            "renderer": renderer,
            "model_dm": model_displayable_manager,
            "volume_dm": volume_displayable_manager,
        }

    def capabilities_summary(self, render_window):
        capabilities = render_window.ReportCapabilities() or ""
        keys = {
            "OpenGL vendor string": "opengl_vendor",
            "OpenGL renderer string": "opengl_renderer",
            "OpenGL version string": "opengl_version",
            "EGL vendor string": "egl_vendor",
        }
        result = {}
        for line in capabilities.splitlines():
            line = line.strip()
            for prefix, key in keys.items():
                if line.startswith(prefix):
                    _, value = line.split(":", 1)
                    result[key] = value.strip()
        return result

    def collect_environment(self, view_bundle):
        render_window = view_bundle["render_window"]
        interactor = render_window.GetInteractor()
        view_node = view_bundle["view_node"]
        quality = safe_call(view_node, "GetVolumeRenderingQuality", 0)
        raycast = safe_call(view_node, "GetRaycastTechnique", 0)
        return {
            "display": os.environ.get("DISPLAY"),
            "qt_qpa_platform": os.environ.get("QT_QPA_PLATFORM"),
            "render_window_class": render_window.GetClassName(),
            "interactor_class": interactor.GetClassName() if interactor else None,
            "desired_update_rate": safe_call(interactor, "GetDesiredUpdateRate", 0.0),
            "still_update_rate": safe_call(interactor, "GetStillUpdateRate", 0.0),
            "view_node_id": view_node.GetID(),
            "view_node_name": view_node.GetName(),
            "use_depth_peeling": bool(safe_call(view_node, "GetUseDepthPeeling", 0)),
            "shadows_visibility": bool(safe_call(view_node, "GetShadowsVisibility", 0)),
            "fps_visible": bool(safe_call(view_node, "GetFPSVisible", 0)),
            "volume_rendering_quality": {
                "value": int(quality or 0),
                "label": slicer.vtkMRMLViewNode.GetVolumeRenderingQualityAsString(int(quality or 0)),
            },
            "raycast_technique": {
                "value": int(raycast or 0),
                "label": slicer.vtkMRMLViewNode.GetRaycastTechniqueAsString(int(raycast or 0)),
            },
            "volume_rendering_oversampling_factor": safe_call(
                view_node, "GetVolumeRenderingOversamplingFactor", 0.0
            ),
            "volume_rendering_surface_smoothing": bool(
                safe_call(view_node, "GetVolumeRenderingSurfaceSmoothing", 0)
            ),
            "capabilities": self.capabilities_summary(render_window),
        }

    def collect_model_items(self, view_bundle):
        view_node_id = view_bundle["view_node"].GetID()
        items = []
        for model_node in slicer.util.getNodesByClass("vtkMRMLModelNode"):
            display_node = None
            for index in range(model_node.GetNumberOfDisplayNodes()):
                candidate = model_node.GetNthDisplayNode(index)
                if not candidate or not candidate.IsA("vtkMRMLModelDisplayNode"):
                    continue
                if candidate.GetVisibility(view_node_id):
                    display_node = candidate
                    break
            if not display_node:
                continue
            items.append(
                {
                    "node": model_node,
                    "display_node": display_node,
                    "node_id": model_node.GetID(),
                    "name": model_node.GetName(),
                    "original_visibility_3d": get_display_visibility_3d(display_node),
                }
            )
        return items

    def collect_volume_items(self, view_bundle):
        view_node = view_bundle["view_node"]
        view_node_id = view_node.GetID()
        volume_rendering_logic = slicer.modules.volumerendering.logic()
        items = []
        for volume_node in slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode"):
            display_node = volume_rendering_logic.GetVolumeRenderingDisplayNodeForViewNode(volume_node, view_node)
            if not display_node or not display_node.GetVisibility(view_node_id):
                continue
            items.append(
                {
                    "node": volume_node,
                    "display_node": display_node,
                    "node_id": volume_node.GetID(),
                    "name": volume_node.GetName(),
                    "original_visibility_3d": get_display_visibility_3d(display_node),
                }
            )
        return items

    def collect_inventory(self, view_bundle):
        model_items = self.collect_model_items(view_bundle)
        volume_items = self.collect_volume_items(view_bundle)
        self.internal_items = {"models": model_items, "volumes": volume_items}
        total_model_points = 0
        total_model_cells = 0
        for item in model_items:
            mesh = safe_call(item["display_node"], "GetOutputMesh")
            mesh_stats = dataset_stats(mesh)
            total_model_points += mesh_stats["points"]
            total_model_cells += mesh_stats["cells"]
        inventory = {
            "model_count": len(model_items),
            "volume_count": len(volume_items),
            "total_model_points": total_model_points,
            "total_model_cells": total_model_cells,
            "model_names": [item["name"] for item in model_items],
            "volume_names": [item["name"] for item in volume_items],
        }
        return inventory

    def set_scenario_visibility(self, models_visible, volumes_visible):
        for item in self.internal_items["models"]:
            set_display_visibility_3d(item["display_node"], models_visible)
        for item in self.internal_items["volumes"]:
            set_display_visibility_3d(item["display_node"], volumes_visible)

    def restore_visibility(self):
        for item in self.internal_items["models"]:
            set_display_visibility_3d(item["display_node"], item["original_visibility_3d"])
        for item in self.internal_items["volumes"]:
            set_display_visibility_3d(item["display_node"], item["original_visibility_3d"])

    def sample_render_metrics(self, view_bundle, label):
        render_window = view_bundle["render_window"]
        renderer = view_bundle["renderer"]
        self.process_events()
        renderer.ResetCameraClippingRange()

        for _ in range(self.warmup_frames):
            render_window.Render()
            self.process_events()

        wall_times_ms = []
        renderer_times_ms = []
        for _ in range(self.measured_frames):
            start = time.perf_counter()
            render_window.Render()
            self.process_events()
            wall_times_ms.append((time.perf_counter() - start) * 1000.0)
            renderer_times_ms.append(renderer.GetLastRenderTimeInSeconds() * 1000.0)

        return {
            "label": label,
            "warmup_frames": self.warmup_frames,
            "measured_frames": self.measured_frames,
            "avg_wall_ms": round(safe_mean(wall_times_ms), 3),
            "median_wall_ms": round(safe_median(wall_times_ms), 3),
            "max_wall_ms": round(max(wall_times_ms) if wall_times_ms else 0.0, 3),
            "avg_renderer_ms": round(safe_mean(renderer_times_ms), 3),
            "median_renderer_ms": round(safe_median(renderer_times_ms), 3),
            "max_renderer_ms": round(max(renderer_times_ms) if renderer_times_ms else 0.0, 3),
            "wall_stdev_ms": round(safe_stdev(wall_times_ms), 3),
            "renderer_stdev_ms": round(safe_stdev(renderer_times_ms), 3),
        }

    def collect_model_metrics(self, view_bundle):
        model_dm = view_bundle["model_dm"]
        metrics = []
        for item in self.internal_items["models"]:
            node = item["node"]
            display_node = item["display_node"]
            actor = model_dm.GetActorByID(node.GetID()) if model_dm else None
            mapper = actor.GetMapper() if actor and hasattr(actor, "GetMapper") else None
            mesh = safe_call(display_node, "GetOutputMesh")
            data = {
                "name": node.GetName(),
                "node_id": node.GetID(),
                "display_node_id": display_node.GetID(),
                "opacity": safe_call(display_node, "GetOpacity", 1.0),
                "scalar_visibility": bool(safe_call(display_node, "GetScalarVisibility", 0)),
                "actor_class": actor.GetClassName() if actor else None,
                "mapper_class": mapper.GetClassName() if mapper else None,
                "mapper_time_to_draw_ms": round((safe_call(mapper, "GetTimeToDraw", 0.0) or 0.0) * 1000.0, 3),
                "estimated_render_time_ms": round((safe_call(actor, "GetEstimatedRenderTime", 0.0) or 0.0) * 1000.0, 3),
                "visibility_3d_after_probe": visibility_label(get_display_visibility_3d(display_node)),
            }
            data.update(dataset_stats(mesh))
            metrics.append(data)
        metrics.sort(key=lambda item: item.get("cells", 0), reverse=True)
        return metrics

    def collect_volume_metrics(self, view_bundle):
        volume_dm = view_bundle["volume_dm"]
        metrics = []
        for item in self.internal_items["volumes"]:
            node = item["node"]
            display_node = item["display_node"]
            actor = volume_dm.GetVolumeActor(node) if volume_dm else None
            mapper = volume_dm.GetVolumeMapper(node) if volume_dm else None
            image_data = node.GetImageData()
            volume_property_node = safe_call(display_node, "GetVolumePropertyNode")
            volume_property = volume_property_node.GetVolumeProperty() if volume_property_node else None
            dims = list(image_data.GetDimensions()) if image_data else [0, 0, 0]
            metrics.append(
                {
                    "name": node.GetName(),
                    "node_id": node.GetID(),
                    "display_node_id": display_node.GetID(),
                    "dimensions": dims,
                    "spacing": [round(value, 4) for value in node.GetSpacing()],
                    "scalar_range": [
                        round(value, 4) for value in (image_data.GetScalarRange() if image_data else (0.0, 0.0))
                    ],
                    "actor_class": actor.GetClassName() if actor else None,
                    "mapper_class": mapper.GetClassName() if mapper else None,
                    "sample_distance": safe_call(mapper, "GetSampleDistance", None),
                    "image_sample_distance": safe_call(mapper, "GetImageSampleDistance", None),
                    "auto_adjust_sample_distances": bool(safe_call(mapper, "GetAutoAdjustSampleDistances", 0)),
                    "lock_sample_distance_to_input_spacing": bool(
                        safe_call(mapper, "GetLockSampleDistanceToInputSpacing", 0)
                    ),
                    "use_jittering": bool(safe_call(mapper, "GetUseJittering", 0)),
                    "max_memory_in_bytes": int(safe_call(mapper, "GetMaxMemoryInBytes", 0) or 0),
                    "max_memory_fraction": safe_call(mapper, "GetMaxMemoryFraction", 0.0),
                    "mapper_time_to_draw_ms": round((safe_call(mapper, "GetTimeToDraw", 0.0) or 0.0) * 1000.0, 3),
                    "estimated_render_time_ms": round((safe_call(actor, "GetEstimatedRenderTime", 0.0) or 0.0) * 1000.0, 3),
                    "allocated_render_time_ms": round((safe_call(actor, "GetAllocatedRenderTime", 0.0) or 0.0) * 1000.0, 3),
                    "cropping_enabled": bool(safe_call(display_node, "GetCroppingEnabled", 0)),
                    "shading_enabled": bool(safe_call(volume_property, "GetShade", 0)),
                    "visibility_3d_after_probe": visibility_label(get_display_visibility_3d(display_node)),
                }
            )
        return metrics

    def analyze_bottleneck(self, scenarios):
        empty_ms = scenarios["empty"]["avg_renderer_ms"]
        models_ms = max(0.0, scenarios["models_only"]["avg_renderer_ms"] - empty_ms)
        volumes_ms = max(0.0, scenarios["volumes_only"]["avg_renderer_ms"] - empty_ms)
        combined_ms = max(0.0, scenarios["combined"]["avg_renderer_ms"] - empty_ms)
        dominant = "baseline or untracked props"
        rationale = "No tracked model or volume rendering cost stood out."

        if not self.internal_items["models"] and not self.internal_items["volumes"]:
            dominant = "no tracked props"
            rationale = "The target view did not contain visible vtkMRMLModelNode actors or volume rendering nodes."
        elif combined_ms <= 0.0 and max(models_ms, volumes_ms) <= 0.0:
            dominant = "baseline or untracked props"
            rationale = "Measured renderer time stayed at the baseline across the isolated scenarios."
        else:
            max_component = max(models_ms, volumes_ms)
            mixed_penalty = combined_ms - max_component
            if max_component > 0.0 and mixed_penalty > max_component * 0.2:
                dominant = "shared renderer penalty"
                rationale = (
                    "The combined render path is noticeably slower than either isolated component, which points to "
                    "extra compositing, fill-rate, depth-buffer, or shading interaction cost in the shared 3D view."
                )
            elif volumes_ms >= models_ms:
                dominant = "volume rendering"
                rationale = (
                    "The isolated volume-rendering scenario consumed at least as much renderer time as the isolated "
                    "model scenario, so the volume mapper is the primary suspect."
                )
            else:
                dominant = "model geometry"
                rationale = (
                    "The isolated model scenario consumed more renderer time than the isolated volume-rendering "
                    "scenario, so polygonal model drawing is the primary suspect."
                )

        recommendations = []
        if dominant == "volume rendering":
            recommendations.append(
                "Inspect volume mapper sample distance, image sample distance, and GPU memory limits before tuning model assets."
            )
            recommendations.append(
                "Check whether view-level volume rendering quality, oversampling factor, or shadows are higher than needed."
            )
        elif dominant == "model geometry":
            recommendations.append(
                "Inspect the largest model cell counts and mapper draw times; decimation or visibility culling is likely more useful than volume tweaks."
            )
            recommendations.append(
                "Transparent models can amplify cost in the same 3D view, so pay attention to model opacity and depth peeling."
            )
        elif dominant == "shared renderer penalty":
            recommendations.append(
                "Inspect mixed-scene settings such as depth peeling, shadows, translucent model opacity, and shared fill-rate pressure."
            )
            recommendations.append(
                "Compare the combined scenario again with shadows disabled and with opaque model displays to isolate compositing overhead."
            )
        else:
            recommendations.append(
                "If the scene is still visibly slow, expand tracing to other displayable-manager types such as segmentations or markups."
            )

        return {
            "baseline_renderer_ms": round(empty_ms, 3),
            "models_delta_ms": round(models_ms, 3),
            "volumes_delta_ms": round(volumes_ms, 3),
            "combined_delta_ms": round(combined_ms, 3),
            "dominant_bottleneck": dominant,
            "rationale": rationale,
            "recommendations": recommendations,
        }

    def run_scenarios(self, view_bundle):
        scenarios = {}
        scenario_specs = [
            ("empty", False, False),
            ("models_only", True, False),
            ("volumes_only", False, True),
            ("combined", True, True),
        ]
        for name, models_visible, volumes_visible in scenario_specs:
            print_line(
                f"Tracing scenario {name}: models={visibility_label(models_visible)}, "
                f"volumes={visibility_label(volumes_visible)}"
            )
            self.set_scenario_visibility(models_visible, volumes_visible)
            scenarios[name] = self.sample_render_metrics(view_bundle, name)
        self.restore_visibility()
        return scenarios

    def write_json(self):
        if not self.json_path:
            return
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as output:
            json.dump(self.report, output, indent=2, sort_keys=True)

    def write_markdown(self):
        if not self.report_path:
            return
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)

        lines = [
            "# Mixed 3D Rendering Trace Report",
            "",
            f"- Status: `{self.report['status']}`",
            f"- Timestamp (UTC): `{self.report['timestamp_utc']}`",
            f"- Scene path: `{self.report.get('scene_path') or 'synthetic/current scene'}`",
            f"- Synthetic scene: `{self.report.get('synthetic_scene')}`",
            "",
            "## Environment",
            "",
        ]

        environment = self.report.get("environment", {})
        for key in [
            "display",
            "qt_qpa_platform",
            "render_window_class",
            "interactor_class",
            "desired_update_rate",
            "still_update_rate",
            "view_node_id",
            "view_node_name",
            "use_depth_peeling",
            "shadows_visibility",
        ]:
            lines.append(f"- {key.replace('_', ' ').title()}: `{environment.get(key)}`")

        capabilities = environment.get("capabilities", {})
        if capabilities:
            lines.extend(
                [
                    "",
                    "### OpenGL Summary",
                    "",
                ]
            )
            for key, value in capabilities.items():
                lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")

        inventory = self.report.get("inventory", {})
        lines.extend(
            [
                "",
                "## Inventory",
                "",
                f"- Visible model nodes: `{inventory.get('model_count', 0)}`",
                f"- Visible volume renderings: `{inventory.get('volume_count', 0)}`",
                f"- Total model points: `{inventory.get('total_model_points', 0)}`",
                f"- Total model cells: `{inventory.get('total_model_cells', 0)}`",
            ]
        )

        scenarios = self.report.get("scenarios", {})
        lines.extend(
            [
                "",
                "## Scenario Timings",
                "",
            ]
        )
        for scenario_name in ["empty", "models_only", "volumes_only", "combined"]:
            scenario = scenarios.get(scenario_name)
            if not scenario:
                continue
            lines.append(
                f"- `{scenario_name}`: avg renderer `{scenario['avg_renderer_ms']}` ms, "
                f"avg wall `{scenario['avg_wall_ms']}` ms"
            )

        analysis = self.report.get("analysis", {})
        lines.extend(
            [
                "",
                "## Likely Bottleneck",
                "",
                f"- Dominant bottleneck: `{analysis.get('dominant_bottleneck')}`",
                f"- Rationale: {analysis.get('rationale')}",
            ]
        )
        for recommendation in analysis.get("recommendations", []):
            lines.append(f"- Recommendation: {recommendation}")

        model_metrics = self.report.get("models", [])
        if model_metrics:
            lines.extend(
                [
                    "",
                    "## Model Details",
                    "",
                ]
            )
            for model in model_metrics:
                lines.append(
                    f"- `{model['name']}`: `{model.get('cells', 0)}` cells, "
                    f"`{model.get('points', 0)}` points, mapper `{model.get('mapper_class')}`, "
                    f"draw `{model.get('mapper_time_to_draw_ms')}` ms"
                )

        volume_metrics = self.report.get("volumes", [])
        if volume_metrics:
            lines.extend(
                [
                    "",
                    "## Volume Details",
                    "",
                ]
            )
            for volume in volume_metrics:
                lines.append(
                    f"- `{volume['name']}`: dims `{volume.get('dimensions')}`, mapper `{volume.get('mapper_class')}`, "
                    f"sample distance `{volume.get('sample_distance')}`, image sample distance "
                    f"`{volume.get('image_sample_distance')}`, draw `{volume.get('mapper_time_to_draw_ms')}` ms"
                )

        error_text = self.report.get("error")
        if error_text:
            lines.extend(["", "## Error", "", "```", error_text.rstrip(), "```"])

        with open(self.report_path, "w", encoding="utf-8") as output:
            output.write("\n".join(lines) + "\n")

    def write_outputs(self):
        self.write_json()
        self.write_markdown()
        if self.report_path:
            print_line(f"TRACE_REPORT_PATH={self.report_path}")
        if self.json_path:
            print_line(f"TRACE_JSON_PATH={self.json_path}")
        print_line(f"TRACE_STATUS={self.report['status']}")

    def run(self):
        try:
            self.prepare_scene()
            view_bundle = self.get_view_bundle()
            self.report["environment"] = self.collect_environment(view_bundle)
            self.report["inventory"] = self.collect_inventory(view_bundle)
            self.report["scenarios"] = self.run_scenarios(view_bundle)
            self.report["models"] = self.collect_model_metrics(view_bundle)
            self.report["volumes"] = self.collect_volume_metrics(view_bundle)
            self.report["analysis"] = self.analyze_bottleneck(self.report["scenarios"])
            self.report["status"] = "ok"
        except Exception:
            self.exit_code = 1
            self.report["status"] = "error"
            self.report["error"] = traceback.format_exc()
            print_line(self.report["error"].rstrip())
        finally:
            try:
                self.restore_visibility()
            except Exception:
                pass
            self.write_outputs()
            qt.QTimer.singleShot(0, lambda: slicer.app.exit(self.exit_code))


def start_trace():
    tracer = MixedRenderTracer()
    tracer.run()


qt.QTimer.singleShot(0, start_trace)
