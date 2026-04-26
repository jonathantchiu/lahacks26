import argparse

import cv2
import torch
from PIL import Image
from torchvision import models, transforms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a quick notable inference check")
    parser.add_argument("--model-path", default="ml/models/sentinel_resnet18.pt")
    parser.add_argument("--image-path", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    state = torch.load(args.model_path, map_location="cpu")
    model.load_state_dict(state)
    model.eval()

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    frame_bgr = cv2.imread(args.image_path)
    if frame_bgr is None:
        raise FileNotFoundError(f"Could not read {args.image_path}")
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    x = transform(img).unsqueeze(0)
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0]
    print(f"mundane={probs[0].item():.4f} notable={probs[1].item():.4f}")


if __name__ == "__main__":
    main()
