"""Konfigurasi input RGB dan normalisasi Mask R-CNN dari pipeline lama."""
from detectron2 import model_zoo
from detectron2.config import get_cfg


def config(p, device="cuda"):
    cfg = get_cfg()
    depth = p["backbone_depth"]
    cfg.merge_from_file(model_zoo.get_config_file(f"COCO-InstanceSegmentation/mask_rcnn_R_{depth}_FPN_3x.yaml"))
    cfg.MODEL.DEVICE = device
    cfg.MODEL.WEIGHTS = ""
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 25
    cfg.MODEL.RESNETS.STRIDE_IN_1X1 = True
    cfg.INPUT.FORMAT = "RGB"
    cfg.INPUT.MASK_FORMAT = "bitmask"
    # NORMALISASI: Detectron2 menerapkan parameter ini di dalam model.
    cfg.MODEL.PIXEL_MEAN = [123.675, 116.28, 103.53]
    cfg.MODEL.PIXEL_STD = [58.395, 57.12, 57.375]
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = p["ap_score_threshold"]
    cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = p["nms_threshold"]
    cfg.TEST.DETECTIONS_PER_IMAGE = p["max_detections"]
    return cfg
