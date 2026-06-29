"""MLflow model registry integration for experiment tracking."""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger("health_wallet.registry")

# Lazy MLflow import — don't crash if not installed
_mlflow = None


def _get_mlflow():
    global _mlflow
    if _mlflow is None:
        try:
            import mlflow
            tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "./mlflow_data")
            mlflow.set_tracking_uri(tracking_uri)
            _mlflow = mlflow
            logger.info("MLflow initialized", extra={"tracking_uri": tracking_uri})
        except ImportError:
            logger.warning("MLflow not installed — experiment tracking disabled")
    return _mlflow


def log_inference_experiment(
    model_name: str,
    prompt_version: str,
    prompt: str,
    response: str,
    latency: float,
    tokens: int,
    endpoint: str,
    success: bool,
    extra_params: Optional[dict] = None,
):
    """Log an inference run to MLflow for experiment tracking."""
    mlflow = _get_mlflow()
    if mlflow is None:
        return

    try:
        experiment_name = "health_wallet_inference"
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            mlflow.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=f"{endpoint}_{int(time.time())}"):
            # Parameters
            mlflow.log_param("model", model_name)
            mlflow.log_param("prompt_version", prompt_version)
            mlflow.log_param("endpoint", endpoint)
            mlflow.log_param("success", success)
            if extra_params:
                mlflow.log_params(extra_params)

            # Metrics
            mlflow.log_metric("latency_ms", round(latency * 1000, 1))
            mlflow.log_metric("tokens", tokens)
            if latency > 0 and tokens > 0:
                mlflow.log_metric("tokens_per_sec", round(tokens / latency, 1))

            # Artifacts (truncated for storage)
            mlflow.log_text(prompt[:2000], "prompt.txt")
            mlflow.log_text(response[:2000], "response.txt")

    except Exception as e:
        logger.warning(f"MLflow logging failed: {e}")


def get_experiment_history(limit: int = 20) -> list[dict]:
    """Retrieve recent experiment runs."""
    mlflow = _get_mlflow()
    if mlflow is None:
        return []

    try:
        experiment = mlflow.get_experiment_by_name("health_wallet_inference")
        if experiment is None:
            return []

        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=limit,
        )

        return runs.to_dict("records") if not runs.empty else []

    except Exception as e:
        logger.warning(f"MLflow query failed: {e}")
        return []
