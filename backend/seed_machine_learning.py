"""
Seed script: Machine Learning (Andrew Ng track) roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_machine_learning.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("20202020-2020-2020-2020-202020202020")
TITLE = "Machine Learning (Andrew Ng)"
DESCRIPTION = "Andrew Ng's ML curriculum from linear regression to ensemble methods and unsupervised learning — with the math, intuition, and implementation you need to actually use it."

NODES = [
    # ---------------- Step 1: Math Foundations ----------------
    ("Step 1: Math Foundations", "Linear Algebra", "Vectors, matrices & matrix multiplication", "easy"),
    ("Step 1: Math Foundations", "Linear Algebra", "Transpose, inverse & determinant", "medium"),
    ("Step 1: Math Foundations", "Linear Algebra", "Eigenvalues & eigenvectors — intuition", "hard"),
    ("Step 1: Math Foundations", "Calculus", "Derivatives & partial derivatives", "medium"),
    ("Step 1: Math Foundations", "Calculus", "Chain rule — backprop foundation", "medium"),
    ("Step 1: Math Foundations", "Statistics", "Mean, variance, covariance & distributions", "easy"),
    ("Step 1: Math Foundations", "Statistics", "Bayes' theorem & conditional probability", "medium"),

    # ---------------- Step 2: Supervised Learning — Regression ----------------
    ("Step 2: Supervised — Regression", "Linear Regression", "Model representation & cost function (MSE)", "easy"),
    ("Step 2: Supervised — Regression", "Linear Regression", "Gradient descent — batch, stochastic, mini-batch", "medium"),
    ("Step 2: Supervised — Regression", "Linear Regression", "Feature scaling — normalization & standardization", "easy"),
    ("Step 2: Supervised — Regression", "Linear Regression", "Normal equation vs gradient descent", "medium"),
    ("Step 2: Supervised — Regression", "Polynomial", "Polynomial regression & feature engineering", "medium"),
    ("Step 2: Supervised — Regression", "Regularization", "Overfitting, underfitting & bias-variance tradeoff", "medium"),
    ("Step 2: Supervised — Regression", "Regularization", "L1 (Lasso) & L2 (Ridge) regularization", "medium"),

    # ---------------- Step 3: Supervised Learning — Classification ----------------
    ("Step 3: Supervised — Classification", "Logistic Regression", "Sigmoid function & decision boundary", "medium"),
    ("Step 3: Supervised — Classification", "Logistic Regression", "Cross-entropy loss & gradient descent for logistic", "medium"),
    ("Step 3: Supervised — Classification", "Logistic Regression", "Multi-class — one-vs-all & softmax", "medium"),
    ("Step 3: Supervised — Classification", "Evaluation", "Confusion matrix, precision, recall & F1", "easy"),
    ("Step 3: Supervised — Classification", "Evaluation", "ROC curve & AUC — when accuracy misleads", "medium"),
    ("Step 3: Supervised — Classification", "SVM", "Support Vector Machines — max-margin intuition", "hard"),
    ("Step 3: Supervised — Classification", "SVM", "Kernels — RBF, polynomial & the kernel trick", "hard"),

    # ---------------- Step 4: Neural Networks Intro ----------------
    ("Step 4: Neural Networks Intro", "Architecture", "Neuron model, activation functions & layers", "easy"),
    ("Step 4: Neural Networks Intro", "Architecture", "Forward propagation — vectorized implementation", "medium"),
    ("Step 4: Neural Networks Intro", "Training", "Backpropagation — intuition & chain rule", "hard"),
    ("Step 4: Neural Networks Intro", "Training", "Weight initialization — why zeros fail", "medium"),
    ("Step 4: Neural Networks Intro", "Training", "Hyperparameters — learning rate, layers, units", "medium"),
    ("Step 4: Neural Networks Intro", "Practical", "Train/dev/test split & data mismatch", "easy"),
    ("Step 4: Neural Networks Intro", "Practical", "Debugging ML — learning curves & error analysis", "medium"),

    # ---------------- Step 5: Improving Models ----------------
    ("Step 5: Improving Models", "Optimization", "Momentum, RMSprop & Adam optimizer", "hard"),
    ("Step 5: Improving Models", "Optimization", "Learning rate schedules & warm-up", "medium"),
    ("Step 5: Improving Models", "Regularization", "Dropout — training vs inference behaviour", "medium"),
    ("Step 5: Improving Models", "Regularization", "Batch normalization — why it helps", "hard"),
    ("Step 5: Improving Models", "Strategy", "Orthogonalization — tune one knob at a time", "medium"),
    ("Step 5: Improving Models", "Strategy", "Error analysis — ceiling analysis & prioritization", "medium"),

    # ---------------- Step 6: Unsupervised Learning ----------------
    ("Step 6: Unsupervised Learning", "Clustering", "K-Means — algorithm, cost & choosing K", "medium"),
    ("Step 6: Unsupervised Learning", "Clustering", "DBSCAN & hierarchical clustering", "medium"),
    ("Step 6: Unsupervised Learning", "Dimensionality Reduction", "PCA — variance explained & reconstruction", "hard"),
    ("Step 6: Unsupervised Learning", "Dimensionality Reduction", "t-SNE & UMAP — visualization", "medium"),
    ("Step 6: Unsupervised Learning", "Anomaly Detection", "Gaussian anomaly detection & threshold tuning", "medium"),

    # ---------------- Step 7: Ensemble Methods ----------------
    ("Step 7: Ensemble Methods", "Trees", "Decision trees — Gini, entropy & pruning", "medium"),
    ("Step 7: Ensemble Methods", "Trees", "Random forest — bagging & feature randomness", "medium"),
    ("Step 7: Ensemble Methods", "Boosting", "XGBoost & LightGBM — gradient boosting intuition", "hard"),
    ("Step 7: Ensemble Methods", "Boosting", "Stacking & blending ensembles", "hard"),

    # ---------------- Step 8: ML in Practice ----------------
    ("Step 8: ML in Practice", "Pipelines", "scikit-learn pipeline — preprocess + model", "easy"),
    ("Step 8: ML in Practice", "Pipelines", "Cross-validation — k-fold & stratified", "medium"),
    ("Step 8: ML in Practice", "Pipelines", "Hyperparameter tuning — grid search & random search", "medium"),
    ("Step 8: ML in Practice", "Deployment", "Model serialization — pickle & joblib", "easy"),
    ("Step 8: ML in Practice", "Deployment", "Serving ML models — REST API with FastAPI", "medium"),
    ("Step 8: ML in Practice", "Deployment", "Data drift & model monitoring basics", "hard"),
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
