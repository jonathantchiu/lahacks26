import argparse
import json
import random
import urllib.error
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Subset
from torchvision import models

from dataset import SecurityFrameDataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train SentinelAI ResNet-18")
    parser.add_argument("--frames-dir", default="ml/data/frames")
    parser.add_argument("--labels-path", default="ml/labels.json")
    parser.add_argument("--output-dir", default="ml/models")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_loaders(
    dataset: SecurityFrameDataset,
    *,
    frames_dir: str,
    labels_path: str,
    batch_size: int,
    val_ratio: float,
    seed: int,
):
    indices = list(range(len(dataset)))
    rng = random.Random(seed)
    rng.shuffle(indices)

    val_size = max(1, int(len(indices) * val_ratio))
    val_idx = indices[:val_size]
    train_idx = indices[val_size:]
    if not train_idx:
        raise ValueError("Train split is empty. Reduce val_ratio or add more data.")

    train_subset = Subset(dataset, train_idx)
    val_dataset = SecurityFrameDataset(frames_dir, labels_path, augment=False)
    val_subset = Subset(val_dataset, val_idx)

    train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False, num_workers=2)
    return train_loader, val_loader


def build_model(device: torch.device) -> nn.Module:
    try:
        model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    except (urllib.error.URLError, RuntimeError):
        print("Pretrained weight download failed; falling back to random init.")
        model = models.resnet18(weights=None)
    for param in model.parameters():
        param.requires_grad = False
    for param in model.layer4.parameters():
        param.requires_grad = True
    model.fc = nn.Linear(model.fc.in_features, 2)
    return model.to(device)


def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device):
    model.eval()
    loss_sum = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            logits = model(x)
            loss = criterion(logits, y)
            loss_sum += loss.item()
            preds = logits.argmax(dim=1)
            correct += int((preds == y).sum().item())
            total += y.size(0)

    avg_loss = loss_sum / max(1, len(loader))
    acc = correct / max(1, total)
    return avg_loss, acc


def train(args: argparse.Namespace) -> None:
    set_seed(args.seed)
    device = get_device()
    print(f"Using device: {device}")

    dataset = SecurityFrameDataset(args.frames_dir, args.labels_path, augment=True)
    train_loader, val_loader = build_loaders(
        dataset,
        frames_dir=args.frames_dir,
        labels_path=args.labels_path,
        batch_size=args.batch_size,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )

    model = build_model(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    best_path = out_dir / "sentinel_resnet18.pt"
    history_path = out_dir / "training_history.json"

    history = {"train_loss": [], "val_loss": [], "val_acc": []}
    best_val_acc = -1.0

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss_sum = 0.0
        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            train_loss_sum += loss.item()

        train_loss = train_loss_sum / max(1, len(train_loader))
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(
            f"Epoch {epoch:02d}/{args.epochs} "
            f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), best_path)
            print(f"Saved best checkpoint to {best_path}")

    history_path.write_text(json.dumps(history, indent=2))
    print(f"Training complete. Best val_acc={best_val_acc:.4f}")
    print(f"Saved history to {history_path}")


if __name__ == "__main__":
    train(parse_args())
