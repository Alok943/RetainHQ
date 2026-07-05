"""
Seed script: Mathematics for Machine Learning roadmap.

Sub-tracks (phase = step spine): Linear Algebra · Calculus & Optimization · Probability & Statistics.

Node list = the validated node-derivation research run (Gemini Deep Research, 2026-07-05;
prerequisite-subject variant of the prompt — content/research/_ready-prompt-math.md). Audit trail
in content/research/math-for-ml/nodes.md. Applied-intuition only: every node names the ML method
it unlocks (PCA, OLS, backprop, SVM, logistic regression, Naive Bayes) — NOT formal proofs.
Replaced the old "Coming Soon" stub.

Unblocks the SDE->MLE / DA->DS "math gap" (Career Paths sde-mle, da-ds) and is the prerequisite
for the Machine Learning (Andrew Ng) roadmap. Tier mix spans easy->hard, NOT beginner-only.

Idempotent. Run: ./.venv/Scripts/python.exe seed_math_ml.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("90909090-9090-9090-9090-909090909090")
SLUG = "math-for-ml"  # content folder key + URL id; matches content/roadmaps/math-for-ml/
TITLE = "Mathematics for Machine Learning"
DESCRIPTION = "Master the applied linear algebra, calculus, and probability required to understand, derive, and debug ML models."

# (phase, section, title, tier, description)
NODES = [
    # ---- Linear Algebra ----
    ("Linear Algebra", "Vector Space Foundations", "Vector representation & dot product", "easy", "Dot products sum element-wise products, measuring vector alignment - used for cosine similarity in LLM embeddings."),
    ("Linear Algebra", "Vector Space Foundations", "Linear independence & span", "medium", "Linearly dependent features lie in the same span - causing matrix non-invertibility and multicollinearity in OLS."),
    ("Linear Algebra", "Vector Space Foundations", "Matrix rank & null space", "hard", "Rank counts independent rows, while null space maps to zero - determining if linear systems have unique solutions."),
    ("Linear Algebra", "Linear Transformations & Operations", "Linear transformations as matrices", "easy", "Multiplying a matrix by a vector scales/rotates space - representing feedforward layer operations in neural nets."),
    ("Linear Algebra", "Linear Transformations & Operations", "Matrix transpose & symmetric matrices", "medium", "Symmetric matrices equal their transpose - representing covariance matrices which guarantee orthogonal eigenvectors."),
    ("Linear Algebra", "Linear Transformations & Operations", "Matrix inverse & determinant", "hard", "Determinants scale volumes; zero determinant means no inverse - rendering OLS normal equations unsolvable."),
    ("Linear Algebra", "Projections & Orthogonality", "Vector norms L1 & L2", "medium", "L1 sums absolute values favoring sparsity, while L2 sums squares to penalize large weights in model regularization."),
    ("Linear Algebra", "Projections & Orthogonality", "Orthogonality & orthonormal bases", "easy", "Orthogonal vectors are perpendicular with zero dot product - forming independent coordinate axes for PCA projection."),
    ("Linear Algebra", "Projections & Orthogonality", "Projection onto subspaces", "hard", "Projections drop vectors into lower subspaces - defining the optimal projection for PCA and closed-form OLS models."),
    ("Linear Algebra", "Matrix Decompositions", "Eigenvalues & eigenvectors", "medium", "Eigenvectors point where transformations only scale - defining the principal axes of maximum variance in PCA."),
    ("Linear Algebra", "Matrix Decompositions", "Diagonalization of covariance matrices", "hard", "Diagonalization splits a covariance matrix into eigen-axes - allowing PCA to decouple correlated features."),
    ("Linear Algebra", "Matrix Decompositions", "Singular Value Decomposition (SVD)", "hard", "SVD factorizes non-square matrices into latent topics - enabling low-rank approximation in recommender systems."),

    # ---- Calculus & Optimization ----
    ("Calculus & Optimization", "Differential Calculus & Gradients", "Univariate derivative & tangents", "easy", "Derivatives measure local slope - providing the directional step needed to minimize loss in gradient descent."),
    ("Calculus & Optimization", "Differential Calculus & Gradients", "Partial derivatives & gradients", "medium", "Gradients group partial derivatives pointing to steepest ascent - vector-directing updates to minimize model loss."),
    ("Calculus & Optimization", "Differential Calculus & Gradients", "Taylor series approximation", "hard", "Taylor series approximates functions locally - justifying linear gradient descent and quadratic Newton steps."),
    ("Calculus & Optimization", "Vector Calculus & Derivatives", "Jacobian matrix", "hard", "Jacobians collect partial derivatives of vector outputs - mapping gradient propagation across neural network layers."),
    ("Calculus & Optimization", "Vector Calculus & Derivatives", "Hessian matrix & curvature", "hard", "Hessians capture second-order partial derivatives - verifying function convexity and step curvature in optimization."),
    ("Calculus & Optimization", "Vector Calculus & Derivatives", "The multivariable chain rule", "hard", "Chain rule multiplies sequential partial derivatives - enabling weight updates during backpropagation."),
    ("Calculus & Optimization", "Unconstrained Optimization", "Gradient descent & updates", "medium", "Gradient descent subtracts the scaled gradient - adjusting model parameters iteratively to minimize training error."),
    ("Calculus & Optimization", "Unconstrained Optimization", "Learning rates & convergence", "medium", "Learning rate scales gradient updates - balancing fast convergence against overshooting or diverging during training."),
    ("Calculus & Optimization", "Unconstrained Optimization", "Stochastic vs batch updates", "medium", "Batch updates use all data, SGD uses one sample - trading compute efficiency for gradient noise during training."),
    ("Calculus & Optimization", "Constrained & Convex Optimization", "Convexity vs non-convexity", "medium", "Convex functions have one global minimum - guaranteeing gradient descent finds the absolute best model parameters."),
    ("Calculus & Optimization", "Constrained & Convex Optimization", "Lagrange multipliers", "hard", "Lagrange multipliers introduce scalar penalties to optimize objectives along equality constraint boundaries."),
    ("Calculus & Optimization", "Constrained & Convex Optimization", "KKT conditions for SVM", "hard", "KKT conditions generalize Lagrange multipliers to inequality constraints - defining sparse support vectors in SVM."),

    # ---- Probability & Statistics ----
    ("Probability & Statistics", "Fundamental Rules & Conditional Probability", "Conditional probability & independence", "easy", "Conditional probability measures event likelihood given evidence - establishing feature independence in Naive Bayes."),
    ("Probability & Statistics", "Fundamental Rules & Conditional Probability", "Bayes theorem", "medium", "Bayes theorem updates beliefs using likelihood and prior - converting feature likelihoods into posterior classes."),
    ("Probability & Statistics", "Fundamental Rules & Conditional Probability", "Law of total probability", "hard", "Law of total probability sums disjoint conditional slices - normalizing class probabilities for softmax predictions."),
    ("Probability & Statistics", "Random Variables & Distributions", "Discrete & continuous variables", "easy", "Discrete variables list outcomes, continuous use density - selecting Binomial for conversion or Gaussian for error."),
    ("Probability & Statistics", "Random Variables & Distributions", "Expectation & variance", "medium", "Expectation is the long-term average; variance measures spread - balancing bias-variance tradeoff in overfit models."),
    ("Probability & Statistics", "Random Variables & Distributions", "Gaussian distribution & CLT", "hard", "Central Limit Theorem states sample means converge to Gaussian - justifying Z-score normality in anomaly detection."),
    ("Probability & Statistics", "Statistical Estimators & Bounds", "Maximum Likelihood Estimation (MLE)", "medium", "MLE maximizes likelihood of training data given parameters - deriving cross-entropy loss for logistic regression."),
    ("Probability & Statistics", "Statistical Estimators & Bounds", "Maximum A Posteriori (MAP)", "hard", "MAP adds a parameter prior to MLE - mathematically equivalent to adding weight regularization to prevent overfitting."),
    ("Probability & Statistics", "Statistical Estimators & Bounds", "Covariance & correlation", "easy", "Covariance signs relationship direction, correlation scales to [-1, 1] - identifying collinear features in EDA."),
    ("Probability & Statistics", "Statistical Testing & Inference", "Null hypothesis & p-values", "medium", "P-values measure probability of extreme data under H0 - determining if an A/B test variant beats the baseline."),
    ("Probability & Statistics", "Statistical Testing & Inference", "Type I & II errors & power", "hard", "Type I is false positive, Type II is false negative - power measures model ability to detect true positive effects."),
    ("Probability & Statistics", "Statistical Testing & Inference", "A/B testing & sample size", "hard", "Sample size calculations balance power and significance - deciding how many users are needed for a valid experiment."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, slug, title, description, created_at) VALUES (:id, :slug, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
