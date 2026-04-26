import json
from pathlib import Path

from PIL import Image
from torch import Tensor
from torch.utils.data import Dataset
from torchvision import transforms


class SecurityFrameDataset(Dataset):
    """Loads frame paths + binary labels from a JSON map."""

    def __init__(self, frames_dir: str, labels_path: str, augment: bool = True) -> None:
        self.frames_dir = Path(frames_dir)
        labels_file = Path(labels_path)
        if not labels_file.exists():
            raise FileNotFoundError(
                f"{labels_file} not found. Generate it with: python ml/label_frames.py"
            )
        labels = json.loads(labels_file.read_text())

        self.samples: list[tuple[Path, int]] = []
        for rel_path, label in labels.items():
            frame_path = self.frames_dir / rel_path
            if frame_path.exists():
                self.samples.append((frame_path, int(label)))

        if not self.samples:
            raise ValueError("No dataset samples found. Check frames_dir and labels_path.")

        self.base_transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        self.aug_transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        self.augment = augment

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[Tensor, Tensor]:
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        transform = self.aug_transform if self.augment and label == 1 else self.base_transform
        x = transform(image)
        import torch

        y = torch.tensor(label, dtype=torch.long)
        return x, y
