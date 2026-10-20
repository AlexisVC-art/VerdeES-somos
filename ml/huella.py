from io import BytesIO
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import models, transforms

_RED = None
_PREPARAR = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


def _red():
    global _RED
    if _RED is None:
        pesos = models.MobileNet_V3_Small_Weights.DEFAULT
        red = models.mobilenet_v3_small(weights=pesos)
        red.classifier = torch.nn.Identity()
        red.eval()
        _RED = red
    return _RED


def _lote(imagenes: list[Image.Image]) -> torch.Tensor:
    return torch.stack([_PREPARAR(imagen) for imagen in imagenes])


def _normalizar(matriz: np.ndarray) -> np.ndarray:
    norma = np.linalg.norm(matriz, axis=1, keepdims=True)
    return matriz / np.maximum(norma, 1e-8)


@torch.inference_mode()
def vectores(rutas: list[Path], grupo: int = 16) -> np.ndarray:
    salida = []
    red = _red()
    for inicio in range(0, len(rutas), grupo):
        imagenes = []
        for ruta in rutas[inicio : inicio + grupo]:
            with Image.open(ruta) as imagen:
                imagenes.append(imagen.convert("RGB").copy())
        matriz = red(_lote(imagenes)).numpy().astype(np.float32)
        salida.append(_normalizar(matriz))
    if not salida:
        return np.zeros((0, 576), dtype=np.float32)
    return np.concatenate(salida, axis=0)


def vector(origen) -> np.ndarray:
    ruta = Path(origen) if not hasattr(origen, "read") else None
    if ruta is not None:
        return vectores([ruta])[0]
    imagen = Image.open(BytesIO(origen.read())).convert("RGB")
    temporal = vectores  # no se usa
    del temporal
    with torch.inference_mode():
        matriz = _red()(_lote([imagen])).numpy().astype(np.float32)
    return _normalizar(matriz)[0]


def parecido(consulta: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    return matriz @ consulta