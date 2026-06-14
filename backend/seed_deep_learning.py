"""
Seed script: Deep Learning roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_deep_learning.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("30303030-3030-3030-3030-303030303030")
TITLE = "Deep Learning"
DESCRIPTION = "Neural networks to Transformers — feedforward, CNNs, RNNs, attention, and modern architectures. Follows the deep learning specialization path (Ng + fast.ai)."

NODES = [
    # ---------------- Step 1: Feedforward Neural Networks ----------------
    ("Step 1: Feedforward Neural Networks", "Foundations", "Perceptron & activation functions (ReLU, sigmoid, tanh)", "easy"),
    ("Step 1: Feedforward Neural Networks", "Foundations", "Forward pass — vectorized multi-layer computation", "medium"),
    ("Step 1: Feedforward Neural Networks", "Foundations", "Loss functions — MSE, cross-entropy & when to use each", "medium"),
    ("Step 1: Feedforward Neural Networks", "Backprop", "Backpropagation — chain rule end-to-end", "hard"),
    ("Step 1: Feedforward Neural Networks", "Backprop", "Vanishing & exploding gradients — diagnosis & fixes", "hard"),
    ("Step 1: Feedforward Neural Networks", "Regularization", "Dropout, L2 & early stopping for NNs", "medium"),
    ("Step 1: Feedforward Neural Networks", "Regularization", "Batch norm — forward & backward pass", "hard"),
    ("Step 1: Feedforward Neural Networks", "Optimization", "Adam, SGD with momentum & learning rate schedules", "medium"),

    # ---------------- Step 2: Convolutional Neural Networks ----------------
    ("Step 2: CNNs", "Operations", "Convolution — kernel, stride, padding & output size", "medium"),
    ("Step 2: CNNs", "Operations", "Pooling layers — max, average & global average", "easy"),
    ("Step 2: CNNs", "Operations", "Receptive field & depth of feature maps", "medium"),
    ("Step 2: CNNs", "Architectures", "LeNet → AlexNet → VGG — evolution of depth", "medium"),
    ("Step 2: CNNs", "Architectures", "ResNet — skip connections & solving depth degradation", "hard"),
    ("Step 2: CNNs", "Architectures", "Inception & DenseNet — multi-scale features", "hard"),
    ("Step 2: CNNs", "Architectures", "MobileNet & EfficientNet — efficient CNNs for edge", "hard"),
    ("Step 2: CNNs", "Applications", "Object detection — R-CNN, YOLO & SSD overview", "hard"),
    ("Step 2: CNNs", "Applications", "Semantic segmentation — U-Net & FCN", "hard"),
    ("Step 2: CNNs", "Transfer Learning", "Fine-tuning pretrained models (ImageNet weights)", "medium"),
    ("Step 2: CNNs", "Transfer Learning", "Feature extraction vs full fine-tuning", "medium"),

    # ---------------- Step 3: Sequence Models (RNN / LSTM) ----------------
    ("Step 3: Sequence Models", "RNNs", "Recurrent neural network — unrolling through time", "medium"),
    ("Step 3: Sequence Models", "RNNs", "Backprop through time (BPTT) & truncated BPTT", "hard"),
    ("Step 3: Sequence Models", "RNNs", "Vanishing gradient in RNNs — why it's worse", "hard"),
    ("Step 3: Sequence Models", "LSTM & GRU", "LSTM — forget, input & output gates", "hard"),
    ("Step 3: Sequence Models", "LSTM & GRU", "GRU — simplified gating & comparison to LSTM", "medium"),
    ("Step 3: Sequence Models", "LSTM & GRU", "Bidirectional & stacked RNNs", "medium"),
    ("Step 3: Sequence Models", "Applications", "Language modelling & character-level RNN", "medium"),
    ("Step 3: Sequence Models", "Applications", "Seq2Seq — encoder-decoder for translation", "hard"),
    ("Step 3: Sequence Models", "Applications", "CTC loss — speech recognition without alignment", "hard"),

    # ---------------- Step 4: Attention & Transformers ----------------
    ("Step 4: Attention & Transformers", "Attention", "Attention mechanism — queries, keys & values", "hard"),
    ("Step 4: Attention & Transformers", "Attention", "Self-attention — how tokens attend to each other", "hard"),
    ("Step 4: Attention & Transformers", "Attention", "Multi-head attention — parallel attention heads", "hard"),
    ("Step 4: Attention & Transformers", "Transformer", "Positional encoding — why order matters", "medium"),
    ("Step 4: Attention & Transformers", "Transformer", "Transformer encoder & decoder architecture", "hard"),
    ("Step 4: Attention & Transformers", "Transformer", "Layer norm, residuals & feed-forward sub-layers", "hard"),
    ("Step 4: Attention & Transformers", "Scaling", "BERT — masked LM & next sentence prediction", "hard"),
    ("Step 4: Attention & Transformers", "Scaling", "GPT — autoregressive pretraining & fine-tuning", "hard"),
    ("Step 4: Attention & Transformers", "Scaling", "ViT — applying transformers to image patches", "hard"),

    # ---------------- Step 5: Generative Models ----------------
    ("Step 5: Generative Models", "GANs", "GAN architecture — generator vs discriminator", "hard"),
    ("Step 5: Generative Models", "GANs", "Training GANs — mode collapse & tips", "hard"),
    ("Step 5: Generative Models", "GANs", "DCGAN, CycleGAN & StyleGAN overview", "hard"),
    ("Step 5: Generative Models", "VAEs", "Variational Autoencoder — latent space & ELBO", "hard"),
    ("Step 5: Generative Models", "Diffusion", "Diffusion models — DDPM & score matching intuition", "hard"),

    # ---------------- Step 6: Practical Deep Learning ----------------
    ("Step 6: Practical DL", "Tooling", "PyTorch fundamentals — tensors, autograd & Dataset", "medium"),
    ("Step 6: Practical DL", "Tooling", "Training loop — optimizer, loss, backward, step", "medium"),
    ("Step 6: Practical DL", "Tooling", "GPU training — .to(device), DataParallel & mixed precision", "medium"),
    ("Step 6: Practical DL", "Tooling", "Experiment tracking — Weights & Biases / TensorBoard", "easy"),
    ("Step 6: Practical DL", "Deployment", "ONNX export & TorchScript for production", "hard"),
    ("Step 6: Practical DL", "Deployment", "Model quantization & pruning basics", "hard"),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)}
        )
        await conn.execute(
            text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)}
        )
        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes (id, roadmap_id, phase, section, title, tier, order_index) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
