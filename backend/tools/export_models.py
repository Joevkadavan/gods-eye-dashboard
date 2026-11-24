"""
export_models.py
================
Reproducible model export for GOD'S EYE.

Produces, from the official COCO-pretrained checkpoints:

    models/yolov8n.onnx          dynamic H/W, FP32   (primary detector)
    models/yolov8n-pose.onnx     dynamic H/W, FP32   (optional pose evidence)
    models/yolov8n.int8.onnx     dynamic H/W, INT8 weight-only quantised

`torch` and `ultralytics` are **build-time only** dependencies: the running
service uses `onnxruntime` exclusively, so the runtime image never needs PyTorch.

Why dynamic shapes
------------------
A static 640x640 export fixes the anchor grid at 8400 cells, so the operator
cannot trade accuracy for latency. Exporting with ``dynamic=True`` keeps the
spatial dims symbolic, which is what makes the "processing resolution" setting
in System Settings real rather than cosmetic.

Usage
-----
    python tools/export_models.py [--models yolov8n yolov8n-pose]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "models"


def export(name: str, opset: int = 12, imgsz: int = 640) -> Path:
    import torch
    from ultralytics import YOLO

    # PyTorch 2.9 switched torch.onnx.export's default to the new dynamo
    # exporter. Ultralytics 8.3's graph uses scalar .item() operations that
    # dynamo cannot export; explicitly use the stable TorchScript exporter.
    original_export = torch.onnx.export

    def legacy_export(*args, **kwargs):
        kwargs.setdefault("dynamo", False)
        return original_export(*args, **kwargs)

    torch.onnx.export = legacy_export
    weights = name if name.endswith(".pt") else f"{name}.pt"
    model = YOLO(weights)
    out = model.export(
        format="onnx",
        imgsz=imgsz,
        dynamic=True,          # <- symbolic H/W
        simplify=False,        # onnxslim not required; keeps the graph honest
        opset=opset,
        batch=1,
        device="cpu",
    )
    torch.onnx.export = original_export
    produced = Path(out)
    if produced.parent != MODELS_DIR:
        target = MODELS_DIR / produced.name
        produced.replace(target)
        produced = target
    print(f"[ok] exported {produced} ({produced.stat().st_size / 1e6:.1f} MB)")
    return produced


def quantize_int8(src: Path, dst: Path) -> None:
    """Weight-only INT8 quantisation (no calibration data required).

    This is the variant an operator would pick for a Raspberry Pi class device:
    activations stay FP32, weights drop to 8-bit, which cuts memory bandwidth
    and model size roughly 4x at a small accuracy cost that is measured in
    docs/evaluation.md.
    """
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(str(src), str(dst), weight_type=QuantType.QInt8)
    print(f"[ok] quantised {dst} ({dst.stat().st_size / 1e6:.1f} MB)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+", default=["yolov8n", "yolov8n-pose"])
    args = ap.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name in args.models:
        export(name)

    if "yolov8n" in args.models:
        quantize_int8(MODELS_DIR / "yolov8n.onnx", MODELS_DIR / "yolov8n.int8.onnx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
