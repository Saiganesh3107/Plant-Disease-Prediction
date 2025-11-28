import matplotlib
matplotlib.use('Agg')
import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import os
import matplotlib.pyplot as plt
import json
import albumentations as A
from albumentations.pytorch import ToTensorV2
import timm

# -------------------- MODEL LOADING -------------------- #
def load_models(model_paths):
    """
    Loads Vision Transformer model (ViT) using timm, configured for 6 output classes.
    """
    models = {}
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"✅ Using device: {device}")

    # Your model has 6 classes
    base_model = timm.create_model('vit_base_patch16_224', pretrained=True, num_classes=6)

    if os.path.exists(model_paths['base']):
        try:
            state_dict = torch.load(model_paths['base'], map_location=device)
            missing, unexpected = base_model.load_state_dict(state_dict, strict=False)
            print(f"✅ Model loaded: {model_paths['base']}")
            if not missing and not unexpected:
                print("✅ All model weights loaded successfully.")
            else:
                print(f"⚠️ Adjusted model keys ({len(missing)} missing, {len(unexpected)} unexpected)")
        except Exception as e:
            print("❌ Error loading model:", e)
    else:
        print("⚠️ Model not found:", model_paths['base'])

    base_model.to(device)
    base_model.eval()
    models['base'] = base_model
    models['device'] = device
    return models


# -------------------- IMAGE PREPROCESS -------------------- #
def preprocess_image(image_path):
    """
    Preprocesses the image using Albumentations (Resize + Normalize + ToTensorV2)
    """
    image = np.array(Image.open(image_path).convert('RGB'))

    transform = A.Compose([
        A.Resize(224, 224),
        A.Normalize(mean=(0.485, 0.456, 0.406),
                    std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ])

    transformed = transform(image=image)
    tensor = transformed["image"].unsqueeze(0)  # Add batch dimension
    img_pil = Image.fromarray(image)
    return tensor, img_pil


# -------------------- SALIENCY MAP -------------------- #
def compute_saliency_map(model, image_tensor):
    """
    Computes saliency map from gradients (visual explanation).
    """
    image_tensor.requires_grad_()
    output = model(image_tensor)
    pred_class = output.argmax(dim=1)
    score = output[0, pred_class]
    score.backward()

    saliency, _ = torch.max(image_tensor.grad.data.abs(), dim=1)
    saliency = saliency.squeeze().cpu().numpy()
    saliency = (saliency - saliency.min()) / (saliency.max() + 1e-9)
    return saliency


# -------------------- SEVERITY ESTIMATION -------------------- #
def estimate_severity_from_saliency(saliency_map, original_img):
    """
    Estimates the severity percentage based on saliency activation.
    """
    gray = np.array(original_img.convert('L')) / 255.0
    leaf_mask = (gray < 0.95).astype(np.uint8)
    saliency_resized = np.array(
        Image.fromarray((saliency_map * 255).astype(np.uint8)).resize(original_img.size)
    ) / 255.0
    saliency_mask = saliency_resized * leaf_mask
    diseased_pixels = (saliency_mask > 0.25).sum()
    total_leaf_pixels = leaf_mask.sum() if leaf_mask.sum() > 0 else saliency_mask.size
    severity = (diseased_pixels / (total_leaf_pixels + 1e-9)) * 100
    return round(float(severity), 2)


# -------------------- PREDICT FUNCTION -------------------- #
def predict_image(model, image_path, class_file, saliency_dir):
    """
    Predicts the disease class from image and returns results.
    """
    try:
        device = next(model.parameters()).device

        # Load class labels
        with open(class_file, 'r') as f:
            classes = json.load(f)
        classes = {str(k): v for k, v in classes.items()}

        # Preprocess image
        tensor, pil_img = preprocess_image(image_path)
        tensor = tensor.to(device)

        # Model inference
        with torch.no_grad():
            output = model(tensor)
            probs = F.softmax(output, dim=1)[0]

        conf, pred_idx = torch.max(probs, dim=0)
        pred_idx_str = str(pred_idx.item())

        # Get label safely
        if pred_idx_str in classes:
            full_label = classes[pred_idx_str]
        else:
            print(f"⚠️ Unknown class index: {pred_idx_str}")
            full_label = f"Unknown___Class_{pred_idx_str}"

        # Split into leaf and disease
        if "___" in full_label:
            leaf, disease = full_label.split("___", 1)
        else:
            leaf, disease = "Unknown", full_label

        leaf, disease = leaf.strip(), disease.strip()
        confidence = round(conf.item() * 100, 2)

        # Compute saliency map
        tensor_cpu = tensor.detach().cpu().clone().requires_grad_(True)
        saliency = compute_saliency_map(model.cpu(), tensor_cpu)
        severity = estimate_severity_from_saliency(saliency, pil_img)

        # Save saliency overlay
        os.makedirs(saliency_dir, exist_ok=True)
        saliency_name = os.path.basename(image_path).split('.')[0] + "_saliency.png"
        saliency_path = os.path.join(saliency_dir, saliency_name)

        saliency_img = Image.fromarray((saliency * 255).astype(np.uint8)).resize(pil_img.size)
        plt.figure(figsize=(3, 3))
        plt.axis("off")
        plt.imshow(pil_img)
        plt.imshow(saliency_img, cmap='jet', alpha=0.4)
        plt.tight_layout()
        plt.savefig(saliency_path, bbox_inches='tight', pad_inches=0)
        plt.close()

        # Print debug info
        print(f"Predicted Leaf: {leaf}, Disease: {disease}, Confidence: {confidence:.2f}%")

        return {
            "leaf": leaf,
            "disease": disease,
            "confidence": confidence,
            "severity": severity,
            "saliency": saliency_path
        }

    except Exception as e:
        print("❌ Error during prediction:", e)
        return {
            "leaf": "Error",
            "disease": "Error",
            "confidence": 0,
            "severity": 0,
            "saliency": ""
        }
