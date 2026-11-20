"""Warp tunggal dengan topologi referensi pada resolusi resize deterministik."""
import cv2
import numpy as np
import torch
from detectron2.data import transforms as T
from detectron2.structures import BitMasks, Instances


def topology(mask):
    _, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return (0, 0)
    parents = hierarchy[0, :, 3]
    return (int((parents == -1).sum()), int((parents != -1).sum()))


def geometry(h, w, p, angle=0.0, scale=1.0):
    # RESIZE: pertahankan rasio aspek dengan batas sisi panjang.
    nh, nw = T.ResizeShortestEdge.get_output_shape(h, w, p["short_edge"], p["long_edge"])
    steps = [T.ResizeTransform(h, w, nh, nw)]
    # AUGMENTASI GEOMETRIS: skala dan rotasi memakai matriks yang sama untuk citra dan mask.
    sh, sw = max(1, round(nh * scale)), max(1, round(nw * scale))
    steps.append(T.ResizeTransform(nh, nw, sh, sw))
    rotation = T.RotationTransform(sh, sw, angle, expand=True)
    steps.append(rotation)
    oh, ow = rotation.bound_h, rotation.bound_w
    factor = min(1.0, p["long_edge"] / max(oh, ow))
    fh, fw = max(1, round(oh * factor)), max(1, round(ow * factor))
    if factor < 1:
        steps.append(T.ResizeTransform(oh, ow, fh, fw))
    transform = T.TransformList(steps)
    # Kontinu koordinat poligon -> pusat piksel OpenCV (offset setengah piksel).
    source = np.array([[0.5, 0.5], [1.5, 0.5], [0.5, 1.5]], dtype=np.float64)
    target = transform.apply_coords(source.copy()) - 0.5
    matrix = np.column_stack((target[1] - target[0], target[2] - target[0], target[0]))
    return matrix, (fh, fw), transform, factor


def apply(rgb, masks, p, rng, training, forced=None):
    h, w = rgb.shape[:2]
    base_matrix, (base_h, base_w), _, _ = geometry(h, w, p)
    baseline = [cv2.warpAffine(m, base_matrix, (base_w, base_h), flags=cv2.INTER_NEAREST,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=0) for m in masks]
    if not all(m.any() for m in baseline):
        raise ValueError("Instance hilang pada resize deterministik.")
    source_topology = [topology(m) for m in masks]
    reference = [topology(m) for m in baseline]
    resize_changes = [{"instance_index": i, "source_topology": source_topology[i],
                       "resized_topology": reference[i]} for i in range(len(masks))
                      if source_topology[i] != reference[i]]
    attempts = []
    budget = p["geometry_max_attempts"] if training else 1
    accepted = None
    for index in range(budget + (1 if training else 0)):
        fallback = training and index == budget
        if not training or fallback:
            angle, scale = 0.0, 1.0
        elif forced is not None and index == 0:
            angle, scale = forced
        else:
            angle = float(rng.uniform(-p["rotation_degrees"], p["rotation_degrees"]))
            scale = float(rng.uniform(*p["scale_range"]))
        matrix, (oh, ow), transform, cap = geometry(h, w, p, angle, scale)
        warped = [cv2.warpAffine(m, matrix, (ow, oh), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0) for m in masks]
        failures = [i for i, m in enumerate(warped) if not m.any() or topology(m) != reference[i]]
        attempts.append({"angle": angle, "scale": scale, "cap_factor": cap, "fallback_resize_only": fallback,
                         "rejected_instance_indices": failures})
        if not failures:
            accepted = (matrix, (oh, ow), transform, warped)
            break
    if accepted is None:
        raise ValueError(f"Topologi referensi resize tidak terjaga: {attempts}")
    matrix, (oh, ow), transform, warped = accepted
    image = cv2.warpAffine(rgb, matrix, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    # AUGMENTASI PENCAHAYAAN: hanya berlaku pada citra latih.
    photo = {"brightness": 1.0, "contrast": 1.0}
    if training:
        photo = {"brightness": float(rng.uniform(*p["brightness_range"])), "contrast": float(rng.uniform(*p["contrast_range"]))}
        image = T.RandomBrightness(photo["brightness"], photo["brightness"]).get_transform(image).apply_image(image)
        image = T.RandomContrast(photo["contrast"], photo["contrast"]).get_transform(image).apply_image(image)
    return image, warped, transform, {"attempts": attempts, "accepted_attempt": len(attempts), "photometric": photo,
                                     "reference_topology": reference, "resize_topology_changes": resize_changes}


def to_input(rgb, masks, classes, image_id, p, rng, training):
    image, warped, transform, details = apply(rgb, masks, p, rng, training)
    h, w = image.shape[:2]
    bitmasks = BitMasks(torch.from_numpy(np.stack(warped).astype(bool)))
    assert bitmasks.nonempty().all()
    obj = Instances((h, w))
    obj.gt_masks = bitmasks
    obj.gt_boxes = bitmasks.get_bounding_boxes()
    obj.gt_classes = torch.tensor(classes, dtype=torch.int64)
    return {"image": torch.from_numpy(np.ascontiguousarray(image.transpose(2, 0, 1))).float(), "instances": obj, "image_id": image_id}, details


def inference_input(rgb, image_id, p):
    h, w = rgb.shape[:2]
    # Resize biasa tanpa anotasi atau penolakan berdasarkan ground truth.
    # RESIZE: pertahankan rasio aspek dengan batas sisi panjang.
    nh, nw = T.ResizeShortestEdge.get_output_shape(h, w, p["short_edge"], p["long_edge"])
    resized = T.ResizeTransform(h, w, nh, nw).apply_image(rgb)
    return {"image": torch.from_numpy(np.ascontiguousarray(resized.transpose(2, 0, 1))).float(),
            "height": h, "width": w, "image_id": image_id}
