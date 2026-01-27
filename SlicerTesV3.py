#exec(open("/home/orto03/VSCode/SlicerTesV3.py").read())

import slicer
import numpy as np
import cv2
import vtk
import scipy.spatial.distance as ssd
import scipy.cluster.hierarchy as sch

TOLERANCE_MM = 6.0       # Generous tolerance to start with
AXIAL_CLUSTER_RADIUS_MM = 5 # Points closer than this are the "Same Ball"
SAGITTAL_CLUSTER_RADIUS_MM = 5 # Points closer than this are the "Same Ball"
CORONAL_CLUSTER_RADIUS_MM = 6

# List of ALL loaded volumes
all_volumes = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")

if len(all_volumes) > 0:
    # Grab the first one in the list
    volume_node = all_volumes[0]
    print(f"✅ Automatically selected volume: {volume_node.GetName()}")
else:
    print("❌ Error: No volumes found in the scene! Please load your data first.")
    raise ValueError("No data loaded")

display_node = volume_node.GetDisplayNode()

# Array from volume node 
volume_array = slicer.util.arrayFromVolume(volume_node)

auto_min_intensity = -1000 
auto_max_intensity = np.percentile(volume_array, 99.9)
print(f"Auto Max Intensity: {auto_max_intensity}")
auto_max_intensity = max(auto_max_intensity, 3000)
    
print(f"Data Shape: {volume_array.shape}")

# Voxel Spacing
spacing = volume_node.GetSpacing()
x_spacing = spacing[0]
y_spacing = spacing[1]
z_spacing = spacing[2]
print(f"Voxel Spacing: {spacing}")

# Aspect Ratio Correction Factor
aspect_ratio_Axial = y_spacing / x_spacing 
aspect_ratio_Sagittal = z_spacing / y_spacing 
aspect_ratio_Coronal = z_spacing / x_spacing
# print(f"Pixel Spacing: X={x_spacing:.2f}mm, Z={z_spacing:.2f}mm")
print(f"Vertical Stretch Factor Sagittal: {aspect_ratio_Sagittal:.2f}x")
print(f"Vertical Stretch Factor Axial: {aspect_ratio_Axial:.2f}x")
print(f"Vertical Stretch Factor Coronal: {aspect_ratio_Coronal:.2f}x")

# Diducial radius in Axial Plane (pixels) 
exact_radius_px = (6 / 2) / x_spacing
min_radius_px = int(exact_radius_px*0.8) 
max_radius_px = int(exact_radius_px*1.2)
# Diducial radius in Sagittal Plane (pixels)
exact_radius_py = (6 / 2) / y_spacing
min_radius_py = int(exact_radius_py*0.8) 
max_radius_py = int(exact_radius_py*1.2)
# Diducial radius in Coronal Plane (pixels) 
exact_radius_pz = (6 / 2) / z_spacing
min_radius_pz = int(exact_radius_pz*0.5) 
max_radius_pz = int(exact_radius_pz*1.2)


print(f"Spacing = {x_spacing:.3f} mm")
print(f"Exact Radius Target = {exact_radius_px:.2f} px")
print(f"Searching for circles between {min_radius_px} and {max_radius_px} pixels")


fixed_threshold = 3070
adaptive_threshold_offset = np.percentile(volume_array, 90.5)
threshold = max(fixed_threshold, adaptive_threshold_offset)


### AXIAL PLANE
candidate_fiducial_point_Axial = []

# Loop through Z-axis (Axial plane)
circles_found_total = 0

for z_index in range(volume_array.shape[0]):
    raw_image_Axial = volume_array[z_index, :, :].copy()

    threshold_image = raw_image_Axial > threshold
    raw_image_Axial[~threshold_image] = 0  # Set below-threshold pixels to 0
    
    img_visual = np.clip(raw_image_Axial, auto_min_intensity, auto_max_intensity)
    img_8bit = cv2.normalize(img_visual, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    original_height, original_width = img_8bit.shape
    new_height = int(original_height * aspect_ratio_Axial)
    
    # Stretch the image vertically so pixels represent real geometry
    img_resized = cv2.resize(img_8bit, (original_width, new_height), interpolation=cv2.INTER_LINEAR)
    # img_blurred = cv2.GaussianBlur(img_resized, (3, 3), 0) % Dont forget to change everything below to img_blured if you uncomment this

    circle  = cv2.HoughCircles(
        img_resized,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=100,
        param2=10,
        minRadius=int(min_radius_px),
        maxRadius=int(max_radius_px)
    )

    # # --- VISUALIZATION TRANSFORM ---
    # if circle is not None:
    #     img_display = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2BGR)
    #     circles_viz = np.uint16(np.around(circle))
    #     for i in circles_viz[0, :]:
    #         cv2.circle(img_display, (i[0], i[1]), i[2], (0, 255, 0), 2)
    #     cv2.putText(img_display, f"Slice: {z_index} (Corrected)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    #     cv2.imshow("Corrected Aspect Ratio", img_display)
    #     if cv2.waitKey(0) & 0xFF == ord('q'): break
    # # ---------------------------

    if circle is not None:
        
        circle = np.uint16(np.around(circle))
        for i in circle[0,:]:
            # img_display = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2BGR)

            circles_found_total += 1
            x_detected, y_detected, radius = i[0], i[1], i[2]

            x_original = x_detected
            y_original = y_detected / aspect_ratio_Axial # Reverse the vertical stretch

            # Converting IJK to RAS coordinate
            ijk_point = [x_original, y_original, z_index, 1.0]        
            ijk_to_ras = vtk.vtkMatrix4x4()
            volume_node.GetIJKToRASMatrix(ijk_to_ras)
            ras_point = [0.0, 0.0, 0.0, 1.0]
            ijk_to_ras.MultiplyPoint(ijk_point, ras_point)

            candidate_fiducial_point_Axial.append(ras_point)




### SAGITTAL PLANE
candidate_fiducial_point_Sagittal = []
#------- Loop through X-axis (Sagittal plane)
circles_found_total = 0

for x_index in range(volume_array.shape[2]):
    raw_image_Sagittal = volume_array[:, :, x_index].copy()

    threshold_image = raw_image_Sagittal > threshold
    raw_image_Sagittal[~threshold_image] = 0  # Set below-threshold pixels to 0
    
    img_visual = np.clip(raw_image_Sagittal, auto_min_intensity, auto_max_intensity)
    img_8bit = cv2.normalize(img_visual, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    original_height, original_width = img_8bit.shape
    new_height = int(original_height * aspect_ratio_Sagittal)
    
    # Stretch the image vertically so pixels represent real geometry
    img_resized = cv2.resize(img_8bit, (original_width, new_height), interpolation=cv2.INTER_LINEAR)
    # img_blurred = cv2.GaussianBlur(img_resized, (3, 3), 0) % Dont forget to change everything below to img_blured if you uncomment this

    circle  = cv2.HoughCircles(
        img_resized,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=100,
        param2=10,
        minRadius=int(min_radius_py),
        maxRadius=int(max_radius_py)
    )

    # # --- VISUALIZATION TRANSFORM ---
    # if circle is not None:
    #     img_display = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2BGR)
    #     circles_viz = np.uint16(np.around(circle))
    #     for i in circles_viz[0, :]:
    #         cv2.circle(img_display, (i[0], i[1]), i[2], (0, 255, 0), 2)
    #     cv2.putText(img_display, f"Slice: {x_index} (Corrected)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    #     cv2.imshow("Corrected Aspect Ratio", img_display)
    #     if cv2.waitKey(0) & 0xFF == ord('q'): break
    # # ---------------------------

    if circle is not None:
        
        circle = np.uint16(np.around(circle))
        for i in circle[0,:]:
            # img_display = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2BGR)

            circles_found_total += 1
            x_detected, y_detected, radius = i[0], i[1], i[2]

            x_original = x_detected
            y_original = y_detected / aspect_ratio_Sagittal # Reverse the vertical stretch

            # Converting IJK to RAS coordinate
            ijk_point = [x_index, x_original, y_original, 1.0]        
            ijk_to_ras = vtk.vtkMatrix4x4()
            volume_node.GetIJKToRASMatrix(ijk_to_ras)
            ras_point = [0.0, 0.0, 0.0, 1.0]
            ijk_to_ras.MultiplyPoint(ijk_point, ras_point)

            candidate_fiducial_point_Sagittal.append(ras_point)




### CORONAL PLANE
candidate_fiducial_point_Coronal = []
# Loop through j-axis (Coronal plane)
circles_found_total = 0

for j_index in range(volume_array.shape[1]):
    raw_image_Coronal = volume_array[:, j_index, :].copy()

    threshold_image = raw_image_Coronal > threshold
    raw_image_Coronal[~threshold_image] = 0  # Set below-threshold pixels to 0
    
    img_visual = np.clip(raw_image_Coronal, auto_min_intensity, auto_max_intensity)
    img_8bit = cv2.normalize(img_visual, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    original_height, original_width = img_8bit.shape
    new_height = int(original_height * aspect_ratio_Coronal)
    
    # Stretch the image vertically so pixels represent real geometry
    img_resized = cv2.resize(img_8bit, (original_width, new_height), interpolation=cv2.INTER_LINEAR)
    # img_blurred = cv2.GaussianBlur(img_resized, (3, 3), 0) % Dont forget to change everything below to img_blured if you uncomment this

    circle  = cv2.HoughCircles(
        img_resized,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=100,
        param2=10,
        minRadius=int(min_radius_px),
        maxRadius=int(max_radius_px)
    )

    # # --- VISUALIZATION TRANSFORM ---
    # if circle is not None:
    #     img_display = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2BGR)
    #     circles_viz = np.uint16(np.around(circle))
    #     for i in circles_viz[0, :]:
    #         cv2.circle(img_display, (i[0], i[1]), i[2], (0, 255, 0), 2)
    #     cv2.putText(img_display, f"Slice: {j_index} (Corrected)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    #     cv2.imshow("Corrected Aspect Ratio", img_display)
    #     if cv2.waitKey(0) & 0xFF == ord('q'): break
    # # ---------------------------

    if circle is not None:
        
        circle = np.uint16(np.around(circle))
        for i in circle[0,:]:
            # img_display = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2BGR)

            circles_found_total += 1
            x_detected, y_detected, radius = i[0], i[1], i[2]

            x_original = x_detected
            y_original = y_detected / aspect_ratio_Coronal # Reverse the vertical stretch

            # Converting IJK to RAS coordinate
            ijk_point = [x_original, j_index, y_original, 1.0]        
            ijk_to_ras = vtk.vtkMatrix4x4()
            volume_node.GetIJKToRASMatrix(ijk_to_ras)
            ras_point = [0.0, 0.0, 0.0, 1.0]
            ijk_to_ras.MultiplyPoint(ijk_point, ras_point)

            candidate_fiducial_point_Coronal.append(ras_point)



### Combine all Planes Points
all_points = []
for i in candidate_fiducial_point_Axial:
    all_points.append(i[:3] + [i[3], 0])
for i in candidate_fiducial_point_Coronal:
    all_points.append(i[:3] + [i[3], 1])
for i in candidate_fiducial_point_Sagittal:
    all_points.append(i[:3] + [i[3], 2])

all_points = np.array(all_points)
position_points = all_points[:, :3]


### Scipy KDTree Method for Clustering

distance_matrix = ssd.pdist(position_points)
linkage_matrix = sch.linkage(distance_matrix, method="complete")
labels = sch.fcluster(linkage_matrix, t=TOLERANCE_MM, criterion="distance")


candidate_clusters = {}
for label, point in zip(labels, all_points):
    if label not in candidate_clusters:
        candidate_clusters[label] = []
    candidate_clusters[label].append(point)

final_cluster = []
for label, points_cluster in candidate_clusters.items():
    tags = []
    for p in points_cluster:
        tags.append(p[4])
    unique_tags = np.unique(tags)
    if len(unique_tags) == 3:
        final_cluster.append(points_cluster)

#  VISUALIZATION CLUSTERS
# if len(final_cluster) > 0:
#     print(f"\n🟢 SUCCESS: Found {len(final_cluster)} valid clusters.")
    
#     markups_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
#     markups_node.SetName("Validated_Point_Clouds")
    
#     # FIX B: Nested loop to extract points from the groups
#     count = 0
#     for cluster in final_cluster:
#         for point in cluster:
#             # point is [x, y, z, r, t]
#             markups_node.AddControlPoint(point[0], point[1], point[2])
#             markups_node.SetNthControlPointLabel(count, f"C{count}")
#             count += 1
            
# else:
#     print("❌ No valid 3-plane clusters found.")



### SphareFit
final_cluster_centroids = []
for i in range(len(final_cluster)):
    surface_points = []
    cloud_points = final_cluster[i]

    if len(cloud_points) < 3:
        continue

    for point in cloud_points:
        x, y, z = point[0], point[1], point[2]
        r = point[3]
        tag = point[4]

        if tag == 0: # Axial Plane
            surface_points.append([x + r, y, z])
            surface_points.append([x - r, y, z])
            surface_points.append([x, y + r, z])
            surface_points.append([x, y - r, z])
        if tag == 1: # Coronal Plane
            surface_points.append([x + r, y, z])
            surface_points.append([x - r, y, z])
            surface_points.append([x, y, z + r])
            surface_points.append([x, y, z - r])
        if tag == 2: # Sagittal Plane
            surface_points.append([x, y + r, z])
            surface_points.append([x, y - r, z])
            surface_points.append([x, y, z + r])
            surface_points.append([x, y, z - r])
    surface_points = np.array(surface_points)

    N = len(surface_points)
    A = np.zeros((N, 4))
    f = np.zeros((N, 1))
    spX = surface_points[:, 0]
    spY = surface_points[:, 1]
    spZ = surface_points[:, 2]
    A[:, 0] = spX*2
    A[:, 1] = spY*2
    A[:, 2] = spZ*2
    A[:, 3] = 1

    f[:, 0] = spX**2 + spY**2 + spZ**2

    # SphareFit equations
    try:
        coefficients = np.linalg.lstsq(A, f, rcond=None)[0]
        center_x = coefficients[0]
        center_y = coefficients[1]
        center_z = coefficients[2]
        radius_squared = coefficients[3] + center_x**2 + center_y**2 + center_z**2
        radius = np.sqrt(radius_squared)
        final_cluster_centroids.append([center_x[0], center_y[0], center_z[0], radius[0]])
    except np.linalg.LinAlgError:
        print("Failed to solve the system of equations.")
        continue


# ---  FINAL VISUALIZATION  ---
if len(final_cluster_centroids) > 0:
    print(f"\n SUCCESS: Found {len(final_cluster_centroids)} valid spheres.")
    
    markups_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
    markups_node.SetName("SphereFit_Centroids")
    
    # FIX: Loop directly through the centroids (No inner loop needed)
    for i, centroid in enumerate(final_cluster_centroids):
        # centroid is [x, y, z, r]
        x, y, z, r = centroid
        
        markups_node.AddControlPoint(x, y, z)
        markups_node.GetDisplayNode().SetSelectedColor(1, 0, 1) 
        markups_node.SetNthControlPointLabel(i, f"Fit_{i+1}")
            
else:
    print("No valid SphereFit clusters found.")



# ### ERROR CALCULATION
# markups_node = slicer.util.getNode("SphereFit_Centroids")
# true_fiducial_node = slicer.util.getNode("FiducialsTrue")
# num_true_fiducials = true_fiducial_node.GetNumberOfControlPoints()
# num_detected_fiducials = markups_node.GetNumberOfControlPoints()
# position_true_fiducial = true_fiducial_node.GetNthControlPointPositionWorld()
# position_detected_fiducial = markups_node.GetNthControlPointPositionWorld()