import datetime
import json
import os
import time
import traceback

import qt
import slicer
import vtk
from slicer.ScriptedLoadableModule import ScriptedLoadableModule


def print_line(message):
    print(message)
    try:
        import sys

        sys.stdout.flush()
    except Exception:
        pass


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def utc_now_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp():
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def average(total, count):
    return total / count if count else 0.0


def monotonic_now():
    return time.monotonic()


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


def get_app_path(name, fallback):
    value = getattr(slicer.app, name, None)
    if callable(value):
        try:
            return value()
        except Exception:
            return fallback
    return value or fallback


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


def get_scene_nodes_by_class(class_name):
    try:
        return slicer.util.getNodesByClass(class_name)
    except Exception:
        return []


def volume_rendering_display_node_state(display_node, view_node_id):
    volume_node = safe_call(display_node, "GetVolumeNode")
    volume_property_node = safe_call(display_node, "GetVolumePropertyNode")
    try:
        displayable_in_view = bool(display_node.IsDisplayableInView(view_node_id))
    except Exception:
        displayable_in_view = False
    try:
        view_specific_visibility = bool(display_node.GetVisibility(view_node_id))
    except Exception:
        view_specific_visibility = False
    return {
        "display_node_id": display_node.GetID(),
        "display_node_name": display_node.GetName(),
        "display_class": display_node.GetClassName(),
        "volume_node_id": volume_node.GetID() if volume_node else None,
        "volume_node_name": volume_node.GetName() if volume_node else None,
        "visibility": bool(safe_call(display_node, "GetVisibility", 0)),
        "visibility_3d": bool(safe_call(display_node, "GetVisibility3D", 0)),
        "opacity": safe_call(display_node, "GetOpacity", 1.0),
        "displayable_in_view": displayable_in_view,
        "view_specific_visibility": view_specific_visibility,
        "has_volume_property_node": bool(volume_property_node),
    }


def is_volume_rendering_display_node_visible(display_node, view_node_id):
    state = volume_rendering_display_node_state(display_node, view_node_id)
    visible = (
        state["visibility"]
        and state["visibility_3d"]
        and state["opacity"] > 0
        and state["displayable_in_view"]
        and state["volume_node_id"]
        and state["has_volume_property_node"]
    )
    return visible, state


def collect_volume_rendering_candidates(view_node_id, volume_displayable_manager):
    visible_nodes = {}
    diagnostics = []
    for display_node in get_scene_nodes_by_class("vtkMRMLVolumeRenderingDisplayNode"):
        volume_node = safe_call(display_node, "GetVolumeNode")
        mapper = volume_displayable_manager.GetVolumeMapper(volume_node) if (volume_displayable_manager and volume_node) else None
        actor = volume_displayable_manager.GetVolumeActor(volume_node) if (volume_displayable_manager and volume_node) else None
        visible, state = is_volume_rendering_display_node_visible(display_node, view_node_id)
        state["has_volume_actor"] = bool(actor)
        state["has_volume_mapper"] = bool(mapper)
        state["active_in_displayable_manager"] = bool(actor or mapper)
        diagnostics.append(state)
        should_count_as_visible = (
            state["volume_node_id"]
            and state["visibility"]
            and state["visibility_3d"]
            and state["opacity"] > 0
            and state["has_volume_property_node"]
            and (state["view_specific_visibility"] or state["active_in_displayable_manager"])
        )
        state["counted_as_visible"] = bool(should_count_as_visible)
        if should_count_as_visible and state["volume_node_id"] not in visible_nodes:
            visible_nodes[state["volume_node_id"]] = (display_node, state)
    diagnostics.sort(
        key=lambda item: (
            not item["counted_as_visible"],
            not item["active_in_displayable_manager"],
            not item["view_specific_visibility"],
            not item["displayable_in_view"],
            not item["visibility"],
            not item["visibility_3d"],
            not item["has_volume_property_node"],
            item["volume_node_name"] or item["display_node_name"] or "",
        )
    )
    return visible_nodes, diagnostics


def get_dataset_stats(dataset):
    if not dataset:
        return {"points": 0, "cells": 0}
    stats = {
        "points": int(safe_call(dataset, "GetNumberOfPoints", 0) or 0),
        "cells": int(safe_call(dataset, "GetNumberOfCells", 0) or 0),
    }
    if dataset.IsA("vtkPolyData"):
        stats["polys"] = int(safe_call(dataset, "GetNumberOfPolys", 0) or 0)
    return stats


def capability_summary(render_window):
    capabilities = render_window.ReportCapabilities() if render_window else ""
    if not capabilities:
        return {}
    keys = {
        "OpenGL vendor string": "opengl_vendor",
        "OpenGL renderer string": "opengl_renderer",
        "OpenGL version string": "opengl_version",
        "EGL vendor string": "egl_vendor",
    }
    result = {}
    for raw_line in capabilities.splitlines():
        line = raw_line.strip()
        for prefix, key in keys.items():
            if line.startswith(prefix):
                _, value = line.split(":", 1)
                result[key] = value.strip()
    return result


class SessionRenderTraceConfig:
    def __init__(self):
        settings = qt.QSettings()

        env_enabled = os.environ.get("AKSARATOR_SESSION_RENDER_TRACE")
        settings_enabled = settings.value("Developer/SessionRenderTraceEnabled")
        self.enabled = parse_bool(env_enabled, parse_bool(settings_enabled, False))

        cache_root = get_app_path("cachePath", get_app_path("temporaryPath", os.getcwd()))
        settings_output_dir = settings.value("Developer/SessionRenderTraceOutputDir")
        self.output_root = (
            os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_OUTPUT_DIR")
            or settings_output_dir
            or os.path.join(cache_root, "SessionRenderTrace")
        )
        self.snapshot_interval_ms = max(
            100,
            parse_int(
                os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_SNAPSHOT_INTERVAL_MS")
                or settings.value("Developer/SessionRenderTraceSnapshotIntervalMs"),
                1000,
            ),
        )
        self.slow_frame_ms = max(
            1.0,
            parse_float(
                os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_SLOW_FRAME_MS")
                or settings.value("Developer/SessionRenderTraceSlowFrameMs"),
                20.0,
            ),
        )
        self.max_slow_samples = max(
            1,
            parse_int(
                os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_MAX_SLOW_SAMPLES")
                or settings.value("Developer/SessionRenderTraceMaxSlowSamples"),
                25,
            ),
        )
        self.max_detail_items = max(
            1,
            parse_int(
                os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_MAX_DETAIL_ITEMS")
                or settings.value("Developer/SessionRenderTraceMaxDetailItems"),
                5,
            ),
        )
        self.transform_activity_window_ms = max(
            50,
            parse_int(
                os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_TRANSFORM_ACTIVITY_WINDOW_MS")
                or settings.value("Developer/SessionRenderTraceTransformActivityWindowMs"),
                400,
            ),
        )
        self.interaction_activity_window_ms = max(
            50,
            parse_int(
                os.environ.get("AKSARATOR_SESSION_RENDER_TRACE_INTERACTION_ACTIVITY_WINDOW_MS")
                or settings.value("Developer/SessionRenderTraceInteractionActivityWindowMs"),
                400,
            ),
        )

    def as_dict(self):
        return {
            "enabled": self.enabled,
            "output_root": self.output_root,
            "snapshot_interval_ms": self.snapshot_interval_ms,
            "slow_frame_ms": self.slow_frame_ms,
            "max_slow_samples": self.max_slow_samples,
            "max_detail_items": self.max_detail_items,
            "transform_activity_window_ms": self.transform_activity_window_ms,
            "interaction_activity_window_ms": self.interaction_activity_window_ms,
        }


class SessionRenderTraceView:
    def __init__(self, service, widget_index, three_d_widget):
        self.service = service
        self.widget_index = widget_index
        self.widget = three_d_widget
        self.view = None
        self.view_node = None
        self.view_id = None
        self.view_name = f"View-{widget_index}"
        self.render_window = None
        self.renderer = None
        self.model_displayable_manager = None
        self.volume_displayable_manager = None
        self.start_observer = None
        self.end_observer = None
        self.interactor = None
        self.interactor_observers = []
        self.camera_node = None
        self.camera_interaction_observer = None
        self.render_start_time = None
        self.total_frames = 0
        self.total_renderer_ms = 0.0
        self.total_wall_ms = 0.0
        self.max_renderer_ms = 0.0
        self.max_wall_ms = 0.0
        self.scenario_stats = {}
        self.state_stats = {}
        self.slow_frames = []
        self.current_snapshot = None
        self.latest_frame_snapshot = None
        self.is_ready = False
        self.interaction_event_count = 0
        self.interaction_button_down = False
        self.last_interaction_time = None

        self.view = three_d_widget.threeDView()
        self.view_node = three_d_widget.mrmlViewNode()
        self.view_id = self.view_node.GetID()
        self.view_name = self.view_node.GetName() or self.view_name
        self.render_window = self.view.renderWindow()
        renderers = self.render_window.GetRenderers() if self.render_window else None
        self.renderer = renderers.GetFirstRenderer() if renderers else None
        self.model_displayable_manager = self.view.displayableManagerByClassName("vtkMRMLModelDisplayableManager")
        self.volume_displayable_manager = self.view.displayableManagerByClassName("vtkMRMLVolumeRenderingDisplayableManager")
        self.current_snapshot = self.capture_snapshot()
        if self.render_window:
            self.interactor = self.render_window.GetInteractor()
            self.start_observer = self.render_window.AddObserver(vtk.vtkCommand.StartEvent, self.on_render_start)
            self.end_observer = self.render_window.AddObserver(vtk.vtkCommand.EndEvent, self.on_render_end)
        self.install_interaction_observers()
        self.is_ready = True

    def stop(self):
        if self.render_window and self.start_observer is not None:
            self.render_window.RemoveObserver(self.start_observer)
        if self.render_window and self.end_observer is not None:
            self.render_window.RemoveObserver(self.end_observer)
        self.start_observer = None
        self.end_observer = None
        if self.camera_node and self.camera_interaction_observer is not None:
            self.camera_node.RemoveObserver(self.camera_interaction_observer)
        self.camera_node = None
        self.camera_interaction_observer = None
        if self.interactor:
            for observer_tag in self.interactor_observers:
                self.interactor.RemoveObserver(observer_tag)
        self.interactor_observers = []
        self.interactor = None

    def install_interaction_observers(self):
        camera_node = self.view.cameraNode() if self.view else None
        if camera_node is not self.camera_node:
            if self.camera_node and self.camera_interaction_observer is not None:
                self.camera_node.RemoveObserver(self.camera_interaction_observer)
            self.camera_node = camera_node
            self.camera_interaction_observer = None
            if self.camera_node:
                self.camera_interaction_observer = self.camera_node.AddObserver(
                    slicer.vtkMRMLCameraNode.CameraInteractionEvent, self.on_camera_interaction
                )
        if not self.interactor or self.interactor_observers:
            return
        for event_id in (
            vtk.vtkCommand.LeftButtonPressEvent,
            vtk.vtkCommand.RightButtonPressEvent,
            vtk.vtkCommand.MiddleButtonPressEvent,
        ):
            self.interactor_observers.append(self.interactor.AddObserver(event_id, self.on_interaction_button_press))
        for event_id in (
            vtk.vtkCommand.LeftButtonReleaseEvent,
            vtk.vtkCommand.RightButtonReleaseEvent,
            vtk.vtkCommand.MiddleButtonReleaseEvent,
        ):
            self.interactor_observers.append(self.interactor.AddObserver(event_id, self.on_interaction_button_release))
        for event_id in (
            vtk.vtkCommand.MouseWheelForwardEvent,
            vtk.vtkCommand.MouseWheelBackwardEvent,
            vtk.vtkCommand.KeyPressEvent,
        ):
            self.interactor_observers.append(self.interactor.AddObserver(event_id, self.on_interaction_signal))

    def mark_interaction(self):
        self.interaction_event_count += 1
        self.last_interaction_time = monotonic_now()

    def on_camera_interaction(self, caller, event):
        self.mark_interaction()

    def on_interaction_button_press(self, caller, event):
        self.interaction_button_down = True
        self.mark_interaction()

    def on_interaction_button_release(self, caller, event):
        self.interaction_button_down = False
        self.mark_interaction()

    def on_interaction_signal(self, caller, event):
        self.mark_interaction()

    def is_interaction_active(self, current_time):
        if self.interaction_button_down:
            return True
        if self.last_interaction_time is None:
            return False
        return (current_time - self.last_interaction_time) <= (
            self.service.config.interaction_activity_window_ms / 1000.0
        )

    def derive_activity_state(self, current_time):
        interaction_active = self.is_interaction_active(current_time)
        tracking_active = self.service.is_tracking_active(current_time)
        if interaction_active and tracking_active:
            return "interaction_and_tracking"
        if tracking_active:
            return "tracking"
        if interaction_active:
            return "interaction"
        return "idle"

    def on_render_start(self, caller, event):
        if not self.is_ready:
            return
        self.render_start_time = time.perf_counter()

    def on_render_end(self, caller, event):
        if not self.is_ready:
            return
        renderer_ms = 0.0
        renderer = self.renderer
        if renderer:
            renderer_ms = float(renderer.GetLastRenderTimeInSeconds()) * 1000.0
        wall_ms = 0.0
        if self.render_start_time is not None:
            wall_ms = (time.perf_counter() - self.render_start_time) * 1000.0
        self.render_start_time = None

        self.total_frames += 1
        self.total_renderer_ms += renderer_ms
        self.total_wall_ms += wall_ms
        self.max_renderer_ms = max(self.max_renderer_ms, renderer_ms)
        self.max_wall_ms = max(self.max_wall_ms, wall_ms)

        current_time = monotonic_now()
        snapshot = dict(self.current_snapshot or self.capture_snapshot())
        scenario = snapshot.get("scenario", "unknown")
        activity_state = self.derive_activity_state(current_time)
        state_label = scenario if scenario == "empty" else f"{scenario}_{activity_state}"
        snapshot["activity_state"] = activity_state
        snapshot["state_label"] = state_label
        snapshot["tracking_active"] = self.service.is_tracking_active(current_time)
        snapshot["interaction_active"] = self.is_interaction_active(current_time)
        snapshot["recent_transform_event_count"] = self.service.recent_transform_event_count(current_time)
        snapshot["recent_transform_nodes"] = self.service.recent_transform_node_names(current_time)
        self.latest_frame_snapshot = snapshot

        stats = self.scenario_stats.setdefault(
            scenario,
            {
                "frame_count": 0,
                "total_renderer_ms": 0.0,
                "total_wall_ms": 0.0,
                "max_renderer_ms": 0.0,
                "max_wall_ms": 0.0,
                "latest_snapshot": snapshot,
            },
        )
        stats["frame_count"] += 1
        stats["total_renderer_ms"] += renderer_ms
        stats["total_wall_ms"] += wall_ms
        stats["max_renderer_ms"] = max(stats["max_renderer_ms"], renderer_ms)
        stats["max_wall_ms"] = max(stats["max_wall_ms"], wall_ms)
        stats["latest_snapshot"] = snapshot

        state_stats = self.state_stats.setdefault(
            state_label,
            {
                "frame_count": 0,
                "total_renderer_ms": 0.0,
                "total_wall_ms": 0.0,
                "max_renderer_ms": 0.0,
                "max_wall_ms": 0.0,
                "latest_snapshot": snapshot,
            },
        )
        state_stats["frame_count"] += 1
        state_stats["total_renderer_ms"] += renderer_ms
        state_stats["total_wall_ms"] += wall_ms
        state_stats["max_renderer_ms"] = max(state_stats["max_renderer_ms"], renderer_ms)
        state_stats["max_wall_ms"] = max(state_stats["max_wall_ms"], wall_ms)
        state_stats["latest_snapshot"] = snapshot

        if max(renderer_ms, wall_ms) >= self.service.config.slow_frame_ms:
            sample = {
                "timestamp_utc": utc_now_iso(),
                "renderer_ms": round(renderer_ms, 3),
                "wall_ms": round(wall_ms, 3),
                "scenario": scenario,
                "state": state_label,
                "activity_state": activity_state,
                "model_count": snapshot.get("model_count", 0),
                "volume_count": snapshot.get("volume_count", 0),
                "recent_transform_event_count": snapshot.get("recent_transform_event_count", 0),
            }
            self.slow_frames.append(sample)
            self.slow_frames.sort(key=lambda item: item["renderer_ms"], reverse=True)
            del self.slow_frames[self.service.config.max_slow_samples :]

    def refresh_snapshot(self):
        self.install_interaction_observers()
        self.current_snapshot = self.capture_snapshot()
        return self.current_snapshot

    def capture_snapshot(self):
        view_node_id = self.view_id
        models = []
        volumes = []
        volume_candidates = []
        total_model_points = 0
        total_model_cells = 0

        for model_node in slicer.util.getNodesByClass("vtkMRMLModelNode"):
            display_node = None
            for display_index in range(model_node.GetNumberOfDisplayNodes()):
                candidate = model_node.GetNthDisplayNode(display_index)
                if not candidate or not candidate.IsA("vtkMRMLModelDisplayNode"):
                    continue
                if candidate.GetVisibility(view_node_id):
                    display_node = candidate
                    break
            if not display_node:
                continue

            actor = self.model_displayable_manager.GetActorByID(display_node.GetID()) if self.model_displayable_manager else None
            mapper = actor.GetMapper() if actor and hasattr(actor, "GetMapper") else None
            mesh = safe_call(display_node, "GetOutputMesh")
            mesh_stats = get_dataset_stats(mesh)
            total_model_points += mesh_stats["points"]
            total_model_cells += mesh_stats["cells"]
            models.append(
                {
                    "name": model_node.GetName(),
                    "node_id": model_node.GetID(),
                    "points": mesh_stats["points"],
                    "cells": mesh_stats["cells"],
                    "polys": mesh_stats.get("polys", 0),
                    "opacity": safe_call(display_node, "GetOpacity", 1.0),
                    "mapper_class": mapper.GetClassName() if mapper else None,
                    "mapper_time_to_draw_ms": round((safe_call(mapper, "GetTimeToDraw", 0.0) or 0.0) * 1000.0, 3),
                }
            )

        visible_volume_nodes, volume_candidate_states = collect_volume_rendering_candidates(
            view_node_id, self.volume_displayable_manager
        )
        for display_node, candidate_state in visible_volume_nodes.values():
            volume_node = safe_call(display_node, "GetVolumeNode")
            if not volume_node:
                continue
            mapper = self.volume_displayable_manager.GetVolumeMapper(volume_node) if self.volume_displayable_manager else None
            actor = self.volume_displayable_manager.GetVolumeActor(volume_node) if self.volume_displayable_manager else None
            image_data = volume_node.GetImageData()
            volumes.append(
                {
                    "name": volume_node.GetName(),
                    "node_id": volume_node.GetID(),
                    "display_node_id": display_node.GetID(),
                    "display_class": display_node.GetClassName(),
                    "dimensions": list(image_data.GetDimensions()) if image_data else [0, 0, 0],
                    "spacing": [round(value, 4) for value in volume_node.GetSpacing()],
                    "mapper_class": mapper.GetClassName() if mapper else None,
                    "sample_distance": safe_call(mapper, "GetSampleDistance", safe_call(display_node, "GetSampleDistance", None)),
                    "image_sample_distance": safe_call(mapper, "GetImageSampleDistance", None),
                    "auto_adjust_sample_distances": bool(safe_call(mapper, "GetAutoAdjustSampleDistances", 0)),
                    "max_memory_in_bytes": int(safe_call(mapper, "GetMaxMemoryInBytes", 0) or 0),
                    "mapper_time_to_draw_ms": round((safe_call(mapper, "GetTimeToDraw", 0.0) or 0.0) * 1000.0, 3),
                    "estimated_render_time_ms": round((safe_call(actor, "GetEstimatedRenderTime", 0.0) or 0.0) * 1000.0, 3),
                    "visibility": candidate_state["visibility"],
                    "visibility_3d": candidate_state["visibility_3d"],
                    "displayable_in_view": candidate_state["displayable_in_view"],
                    "has_volume_property_node": candidate_state["has_volume_property_node"],
                }
            )
        if not volumes:
            volume_candidates = volume_candidate_states[: self.service.config.max_detail_items]

        models.sort(key=lambda item: item.get("cells", 0), reverse=True)
        volumes.sort(key=lambda item: item.get("mapper_time_to_draw_ms", 0.0), reverse=True)

        model_count = len(models)
        volume_count = len(volumes)
        if model_count and volume_count:
            scenario = "combined"
        elif model_count:
            scenario = "models_only"
        elif volume_count:
            scenario = "volumes_only"
        else:
            scenario = "empty"

        view_quality = safe_call(self.view_node, "GetVolumeRenderingQuality", 0)
        raycast = safe_call(self.view_node, "GetRaycastTechnique", 0)
        snapshot = {
            "timestamp_utc": utc_now_iso(),
            "scenario": scenario,
            "model_count": model_count,
            "volume_count": volume_count,
            "total_model_points": total_model_points,
            "total_model_cells": total_model_cells,
            "model_names": [item["name"] for item in models[: self.service.config.max_detail_items]],
            "volume_names": [item["name"] for item in volumes[: self.service.config.max_detail_items]],
            "models": models[: self.service.config.max_detail_items],
            "volumes": volumes[: self.service.config.max_detail_items],
            "volume_rendering_candidates": volume_candidates,
            "use_depth_peeling": bool(safe_call(self.view_node, "GetUseDepthPeeling", 0)),
            "shadows_visibility": bool(safe_call(self.view_node, "GetShadowsVisibility", 0)),
            "volume_rendering_quality": slicer.vtkMRMLViewNode.GetVolumeRenderingQualityAsString(int(view_quality or 0)),
            "raycast_technique": slicer.vtkMRMLViewNode.GetRaycastTechniqueAsString(int(raycast or 0)),
            "volume_rendering_oversampling_factor": safe_call(
                self.view_node, "GetVolumeRenderingOversamplingFactor", 0.0
            ),
        }
        return snapshot

    def summarize(self):
        scenario_summary = {}
        for scenario, stats in self.scenario_stats.items():
            frame_count = stats["frame_count"]
            scenario_summary[scenario] = {
                "frame_count": frame_count,
                "avg_renderer_ms": round(average(stats["total_renderer_ms"], frame_count), 3),
                "avg_wall_ms": round(average(stats["total_wall_ms"], frame_count), 3),
                "max_renderer_ms": round(stats["max_renderer_ms"], 3),
                "max_wall_ms": round(stats["max_wall_ms"], 3),
                "latest_snapshot": stats["latest_snapshot"],
            }
        state_summary = {}
        for state_label, stats in self.state_stats.items():
            frame_count = stats["frame_count"]
            state_summary[state_label] = {
                "frame_count": frame_count,
                "avg_renderer_ms": round(average(stats["total_renderer_ms"], frame_count), 3),
                "avg_wall_ms": round(average(stats["total_wall_ms"], frame_count), 3),
                "max_renderer_ms": round(stats["max_renderer_ms"], 3),
                "max_wall_ms": round(stats["max_wall_ms"], 3),
                "latest_snapshot": stats["latest_snapshot"],
            }

        return {
            "view_id": self.view_id,
            "view_name": self.view_name,
            "widget_index": self.widget_index,
            "render_window_class": self.render_window.GetClassName() if self.render_window else None,
            "capabilities": capability_summary(self.render_window),
            "total_frames": self.total_frames,
            "avg_renderer_ms": round(average(self.total_renderer_ms, self.total_frames), 3),
            "avg_wall_ms": round(average(self.total_wall_ms, self.total_frames), 3),
            "max_renderer_ms": round(self.max_renderer_ms, 3),
            "max_wall_ms": round(self.max_wall_ms, 3),
            "latest_snapshot": self.latest_frame_snapshot or self.current_snapshot,
            "state_summary": state_summary,
            "scenario_summary": scenario_summary,
            "slow_frames": self.slow_frames,
            "interaction_event_count": self.interaction_event_count,
        }


class SessionRenderTraceService:
    def __init__(self, config):
        self.config = config
        self.started = False
        self.finalized = False
        self.start_time = time.time()
        self.start_timestamp_utc = utc_now_iso()
        self.session_stamp = utc_stamp()
        self.view_traces = {}
        self.errors = []
        self.layout_manager = None
        self.transform_observers = {}
        self.last_transform_time = None
        self.transform_event_count = 0
        self.transform_event_log = []
        self.snapshot_timer = qt.QTimer()
        self.snapshot_timer.setInterval(self.config.snapshot_interval_ms)
        self.snapshot_timer.connect("timeout()", self.refresh_snapshots)

    def install(self):
        if not self.config.enabled:
            print_line("SessionRenderTrace: disabled")
            return
        print_line("SessionRenderTrace: enabled")
        slicer.app.connect("startupCompleted()", self.start_if_possible)
        slicer.app.connect("aboutToQuit()", self.finalize)
        qt.QTimer.singleShot(0, self.start_if_possible)

    def start_if_possible(self):
        if self.started or not self.config.enabled:
            return
        if slicer.app.commandOptions().noMainWindow:
            self.errors.append("Application started without a main window; session render trace skipped.")
            return
        self.layout_manager = slicer.app.layoutManager()
        if not self.layout_manager:
            return
        try:
            self.layout_manager.layoutChanged.connect(self.schedule_view_refresh)
        except Exception:
            pass
        self.started = True
        self.refresh_views()
        self.refresh_snapshots()
        self.snapshot_timer.start()
        print_line("SessionRenderTrace: started")

    def schedule_view_refresh(self, *args):
        qt.QTimer.singleShot(0, self.refresh_views)

    def sync_transform_observers(self):
        active_transform_ids = set()
        for transform_node in slicer.util.getNodesByClass("vtkMRMLTransformNode"):
            transform_id = transform_node.GetID()
            active_transform_ids.add(transform_id)
            if transform_id not in self.transform_observers:
                self.transform_observers[transform_id] = (
                    transform_node,
                    transform_node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.on_transform_modified),
                )
        removed_transform_ids = [transform_id for transform_id in self.transform_observers if transform_id not in active_transform_ids]
        for transform_id in removed_transform_ids:
            transform_node, observer_tag = self.transform_observers.pop(transform_id)
            if transform_node and observer_tag is not None:
                transform_node.RemoveObserver(observer_tag)

    def on_transform_modified(self, caller, event):
        event_time = monotonic_now()
        self.last_transform_time = event_time
        self.transform_event_count += 1
        self.transform_event_log.append(
            {
                "time": event_time,
                "node_id": caller.GetID() if caller and hasattr(caller, "GetID") else None,
                "node_name": caller.GetName() if caller and hasattr(caller, "GetName") else None,
            }
        )
        max_events = max(self.config.max_slow_samples * 4, 50)
        del self.transform_event_log[:-max_events]

    def is_tracking_active(self, current_time):
        if self.last_transform_time is None:
            return False
        return (current_time - self.last_transform_time) <= (self.config.transform_activity_window_ms / 1000.0)

    def recent_transform_events(self, current_time):
        window_seconds = self.config.transform_activity_window_ms / 1000.0
        return [item for item in self.transform_event_log if (current_time - item["time"]) <= window_seconds]

    def recent_transform_event_count(self, current_time):
        return len(self.recent_transform_events(current_time))

    def recent_transform_node_names(self, current_time):
        names = []
        for item in self.recent_transform_events(current_time):
            label = item["node_name"] or item["node_id"]
            if label and label not in names:
                names.append(label)
        return names[: self.config.max_detail_items]

    def refresh_views(self):
        if not self.layout_manager:
            return
        self.sync_transform_observers()
        active_view_ids = set()
        for widget_index in range(self.layout_manager.threeDViewCount):
            three_d_widget = self.layout_manager.threeDWidget(widget_index)
            if not three_d_widget:
                continue
            view_node = three_d_widget.mrmlViewNode()
            if not view_node:
                continue
            view_id = view_node.GetID()
            active_view_ids.add(view_id)
            if view_id not in self.view_traces:
                try:
                    self.view_traces[view_id] = SessionRenderTraceView(self, widget_index, three_d_widget)
                except Exception:
                    self.errors.append(traceback.format_exc())
        removed_view_ids = [view_id for view_id in self.view_traces if view_id not in active_view_ids]
        for view_id in removed_view_ids:
            self.view_traces[view_id].stop()
            del self.view_traces[view_id]

    def refresh_snapshots(self):
        if not self.started:
            return
        self.refresh_views()
        for view_trace in self.view_traces.values():
            try:
                view_trace.refresh_snapshot()
            except Exception:
                self.errors.append(traceback.format_exc())

    def stop(self):
        if self.snapshot_timer.isActive():
            self.snapshot_timer.stop()
        for view_trace in list(self.view_traces.values()):
            view_trace.stop()
        self.view_traces = {}
        for transform_node, observer_tag in list(self.transform_observers.values()):
            if transform_node and observer_tag is not None:
                transform_node.RemoveObserver(observer_tag)
        self.transform_observers = {}
        self.started = False

    def analyze(self, views):
        observations = []
        for view in views:
            state_summary = view.get("state_summary", {})
            combined_states = {name: stats for name, stats in state_summary.items() if name.startswith("combined_")}
            if combined_states:
                combined_idle = combined_states.get("combined_idle", {})
                combined_tracking = combined_states.get("combined_tracking", {})
                combined_interaction = combined_states.get("combined_interaction", {})
                if combined_idle and combined_tracking:
                    delta = combined_tracking.get("avg_renderer_ms", 0.0) - combined_idle.get("avg_renderer_ms", 0.0)
                    observations.append(
                        {
                            "view_name": view["view_name"],
                            "result": "tracking overhead observed",
                            "rationale": (
                                f"Combined tracking frames averaged {combined_tracking.get('avg_renderer_ms', 0.0)} ms "
                                f"versus {combined_idle.get('avg_renderer_ms', 0.0)} ms while idle "
                                f"(delta {round(delta, 3)} ms)."
                            ),
                        }
                    )
                    continue
                if combined_idle and combined_interaction:
                    delta = combined_interaction.get("avg_renderer_ms", 0.0) - combined_idle.get("avg_renderer_ms", 0.0)
                    observations.append(
                        {
                            "view_name": view["view_name"],
                            "result": "interaction overhead observed",
                            "rationale": (
                                f"Combined interaction frames averaged {combined_interaction.get('avg_renderer_ms', 0.0)} ms "
                                f"versus {combined_idle.get('avg_renderer_ms', 0.0)} ms while idle "
                                f"(delta {round(delta, 3)} ms)."
                            ),
                        }
                    )
                    continue
                observed_states = ", ".join(sorted(combined_states.keys()))
                observations.append(
                    {
                        "view_name": view["view_name"],
                        "result": "combined baseline captured",
                        "rationale": (
                            f"The session observed {observed_states}, which is operationally relevant, "
                            "but it did not capture enough combined-state diversity for a reliable state-to-state comparison."
                        ),
                    }
                )
                continue
            scenario_summary = view.get("scenario_summary", {})
            combined = scenario_summary.get("combined", {})
            if not combined:
                observations.append(
                    {
                        "view_name": view["view_name"],
                        "result": "insufficient combined scenarios",
                        "rationale": "The session did not observe combined rendering often enough to characterize the real navigation workload.",
                    }
                )
                continue
            observations.append(
                {
                    "view_name": view["view_name"],
                    "result": "combined baseline captured",
                    "rationale": (
                        f"Combined frames averaged {combined.get('avg_renderer_ms', 0.0)} ms, "
                        "but no idle, interaction, or tracking sub-states were captured yet."
                    ),
                }
            )
        return observations

    def build_report(self):
        duration_seconds = max(0.0, time.time() - self.start_time)
        views = [view_trace.summarize() for view_trace in self.view_traces.values()]
        return {
            "status": "ok" if self.started else "not-started",
            "start_timestamp_utc": self.start_timestamp_utc,
            "end_timestamp_utc": utc_now_iso(),
            "duration_seconds": round(duration_seconds, 3),
            "config": self.config.as_dict(),
            "application": {
                "name": slicer.app.applicationName,
                "main_window_present": not slicer.app.commandOptions().noMainWindow,
            },
            "events": {
                "transform_event_count": self.transform_event_count,
                "observed_transform_node_count": len(self.transform_observers),
                "transform_activity_window_ms": self.config.transform_activity_window_ms,
                "interaction_activity_window_ms": self.config.interaction_activity_window_ms,
            },
            "views": views,
            "analysis": self.analyze(views),
            "errors": self.errors,
        }

    def output_directory(self):
        output_dir = os.path.join(self.config.output_root, self.session_stamp)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def write_markdown(self, report, path):
        lines = [
            "# Session Render Trace Report",
            "",
            f"- Status: `{report['status']}`",
            f"- Start (UTC): `{report['start_timestamp_utc']}`",
            f"- End (UTC): `{report['end_timestamp_utc']}`",
            f"- Duration (s): `{report['duration_seconds']}`",
            "",
            "## Configuration",
            "",
        ]
        for key, value in report["config"].items():
            lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")
        events = report.get("events") or {}
        if events:
            lines.extend(["", "## Event Summary", ""])
            for key, value in events.items():
                lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")

        lines.extend(["", "## Views", ""])
        for view in report["views"]:
            lines.append(f"### {view['view_name']}")
            lines.append("")
            lines.append(f"- Total frames: `{view['total_frames']}`")
            lines.append(f"- Avg renderer ms: `{view['avg_renderer_ms']}`")
            lines.append(f"- Avg wall ms: `{view['avg_wall_ms']}`")
            lines.append(f"- Max renderer ms: `{view['max_renderer_ms']}`")
            lines.append(f"- Max wall ms: `{view['max_wall_ms']}`")
            lines.append(f"- Interaction events observed: `{view.get('interaction_event_count', 0)}`")
            latest_snapshot = view.get("latest_snapshot") or {}
            lines.append(f"- Latest scenario: `{latest_snapshot.get('scenario', 'unknown')}`")
            lines.append(f"- Latest activity state: `{latest_snapshot.get('activity_state', 'unknown')}`")
            lines.append(f"- Latest state label: `{latest_snapshot.get('state_label', 'unknown')}`")
            lines.append(f"- Visible models: `{latest_snapshot.get('model_count', 0)}`")
            lines.append(f"- Visible volume renderings: `{latest_snapshot.get('volume_count', 0)}`")
            lines.append(f"- Recent transform events near latest frame: `{latest_snapshot.get('recent_transform_event_count', 0)}`")
            recent_transform_nodes = latest_snapshot.get("recent_transform_nodes", [])
            if recent_transform_nodes:
                lines.append(f"- Recent transform nodes: `{', '.join(recent_transform_nodes)}`")
            scenario_summary = view.get("scenario_summary", {})
            if scenario_summary:
                lines.append("")
                lines.append("Composition summary:")
                for scenario_name, scenario in scenario_summary.items():
                    lines.append(
                        f"- `{scenario_name}`: frames `{scenario['frame_count']}`, "
                        f"avg renderer `{scenario['avg_renderer_ms']}` ms, avg wall `{scenario['avg_wall_ms']}` ms"
                    )
            state_summary = view.get("state_summary", {})
            if state_summary:
                lines.append("")
                lines.append("Operational state summary:")
                for state_name, state in state_summary.items():
                    lines.append(
                        f"- `{state_name}`: frames `{state['frame_count']}`, "
                        f"avg renderer `{state['avg_renderer_ms']}` ms, avg wall `{state['avg_wall_ms']}` ms"
                    )
            slow_frames = view.get("slow_frames", [])
            if slow_frames:
                lines.append("")
                lines.append("Top slow frames:")
                for sample in slow_frames[: self.config.max_detail_items]:
                    lines.append(
                        f"- `{sample['timestamp_utc']}` state `{sample.get('state', sample['scenario'])}` "
                        f"renderer `{sample['renderer_ms']}` ms wall `{sample['wall_ms']}` ms"
                    )
            capabilities = view.get("capabilities") or {}
            if capabilities:
                lines.append("")
                lines.append("OpenGL summary:")
                for key, value in capabilities.items():
                    lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")
            lines.append("")

        lines.extend(["## Analysis", ""])
        for analysis in report["analysis"]:
            lines.append(f"- `{analysis['view_name']}`: `{analysis['result']}`. {analysis['rationale']}")

        if report["errors"]:
            lines.extend(["", "## Errors", ""])
            for error in report["errors"]:
                lines.append("```")
                lines.append(error.rstrip())
                lines.append("```")

        with open(path, "w", encoding="utf-8") as output:
            output.write("\n".join(lines) + "\n")

    def finalize(self):
        if self.finalized or not self.config.enabled:
            return
        self.finalized = True
        try:
            self.refresh_snapshots()
            report = self.build_report()
            output_dir = self.output_directory()
            json_path = os.path.join(output_dir, "session-render-trace.json")
            markdown_path = os.path.join(output_dir, "session-render-trace.md")
            with open(json_path, "w", encoding="utf-8") as output:
                json.dump(report, output, indent=2, sort_keys=True)
            self.write_markdown(report, markdown_path)
            print_line(f"SessionRenderTrace report: {markdown_path}")
            print_line(f"SessionRenderTrace json: {json_path}")
        except Exception:
            print_line("SessionRenderTrace finalize failed")
            print_line(traceback.format_exc().rstrip())
        finally:
            self.stop()


class SessionRenderTrace(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "SessionRenderTrace"
        self.parent.categories = [""]
        self.parent.dependencies = []
        self.parent.contributors = ["Codex"]
        self.parent.hidden = True
        self.parent.helpText = "Hidden background render tracing service."
        self.parent.acknowledgementText = "Background session tracing for mixed 3D rendering telemetry."

        existing_service = getattr(slicer, "sessionRenderTraceService", None)
        if existing_service:
            existing_service.stop()
        slicer.sessionRenderTraceService = SessionRenderTraceService(SessionRenderTraceConfig())
        slicer.sessionRenderTraceService.install()
