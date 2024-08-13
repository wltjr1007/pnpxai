from typing import Literal, Callable, Optional, Type, Union, Tuple

from pnpxai.core.experiment.experiment import Experiment
from pnpxai.core.detector import detect_model_architecture
from pnpxai.core.recommender import XaiRecommender
from pnpxai.core._types import DataSource, Model, ModalityOrListOfModalities, Modality
from pnpxai.explainers.types import TargetLayerOrListOfTargetLayers, ForwardArgumentExtractor
from pnpxai.explainers.utils import (
    get_default_feature_mask_fn,
    get_default_baseline_fn,
)
from pnpxai.explainers.utils.postprocess import (
    PostProcessor,
    all_postprocessors,
)
from pnpxai.evaluator.metrics import PIXEL_FLIPPING_METRICS
from pnpxai.evaluator.metrics import(
    MuFidelity,
    Sensitivity,
    Complexity,
    MoRF,
    LeRF,
    AbPC,
)
from pnpxai.evaluator.metrics.utils import get_default_channel_dim

METRICS_BASELINE_FN_REQUIRED = PIXEL_FLIPPING_METRICS
METRICS_CHANNEL_DIM_REQUIRED = PIXEL_FLIPPING_METRICS
DEFAULT_METRICS = [
    AbPC,
    MoRF,
    LeRF,
    MuFidelity,
    Sensitivity,
    Complexity,
]

class AutoExplanation(Experiment):
    """
    An extension of Experiment class with automatic explainers and evaluation metrics recommendation.

    Parameters:
        model (Model): The machine learning model to be analyzed.
        data (DataSource): The data source used for the experiment.
        task (Literal["image", "tabular"], optional): The task type, either "image" or "tabular". Defaults to "image".
        question (Literal["why", "how"], optional): The type of question the experiment aims to answer, either "why" or "how". Defaults to "why".
        evaluator_enabled (bool, optional): Whether to enable the evaluator. Defaults to True.
        input_extractor (Optional[Callable], optional): Custom function to extract input features. Defaults to None.
        label_extractor (Optional[Callable], optional): Custom function to extract target labels. Defaults to None.
        input_visualizer (Optional[Callable], optional): Custom function for visualizing input features. Defaults to None.
        target_visualizer (Optional[Callable], optional): Custom function for visualizing target labels. Defaults to None.
    """
    def __init__(
        self,
        model: Model,
        data: DataSource,
        modality: ModalityOrListOfModalities = "image",
        input_extractor: Optional[Callable] = None,
        label_extractor: Optional[Callable] = None,
        target_extractor: Optional[Callable] = None,
        target_labels: bool = False,
        input_visualizer: Optional[Callable] = None,
        target_visualizer: Optional[Callable] = None,
        **kwargs,
    ):
        self.modality = modality
        self._check_layer(kwargs)
        self._check_background_data(kwargs)

        self.recommended = XaiRecommender().recommend(modality=modality, model=model)

        super().__init__(
            model=model,
            data=data,
            explainers=self._load_default_explainers(model, kwargs),
            postprocessors=self._load_default_postprocessors(kwargs),
            metrics=self._load_default_metrics(model, kwargs),
            input_extractor=input_extractor,
            label_extractor=label_extractor,
            target_extractor=target_extractor,
            target_labels=target_labels,
            input_visualizer=input_visualizer,
            target_visualizer=target_visualizer,
        )

    def _check_layer(self, kwargs):
        if (self.modality == 'text' or 'text' in self.modality):
            assert kwargs.get('layer'), "Must have 'layer' for text modality. It might be a word embedding layer of your model."
    
    def _check_background_data(self, kwargs):
        if self.modality == 'tabular':
            assert kwargs.get('background_data') is not None, "Must have 'background_data' for tabular modality."

    def _load_default_explainers(self, model, kwargs):
        # explainers
        explainers = []
        for explainer_type in self.recommended.explainers:
            default_kwargs = self._generate_default_kwargs_for_explainer(kwargs)
            if explainer_type.__name__ in ["Lime", "KernelShap"]:
                explainer = explainer_type(model=model, feature_mask_fn=default_kwargs['feature_mask_fn'], baseline_fn=default_kwargs['baseline_fn'])
            else:
                explainer = explainer_type(model=model)
            for k, v in kwargs.items():
                try:
                    explainer.set_kwargs(**{k: v})
                except AttributeError:
                    pass
            explainers.append(explainer)
        return explainers

    def _load_default_postprocessors(self, kwargs):
        channel_dim = kwargs.get('channel_dim') or get_default_channel_dim(self.modality)
        return all_postprocessors(channel_dim)

    def _load_default_metrics(self, model, kwargs):
        channel_dim = kwargs.get('channel_dim') or get_default_channel_dim(self.modality)
        empty_metrics = []
        for metric_type in DEFAULT_METRICS:
            metric_kwargs = {}
            if metric_type in METRICS_BASELINE_FN_REQUIRED:
                metric_kwargs['baseline_fn'] = kwargs.get('baseline_fn') \
                    or get_default_baseline_fn(self.modality, mask_token_id=kwargs.get('mask_token_id') or 0)
            if metric_type in METRICS_CHANNEL_DIM_REQUIRED:
                metric_kwargs['channel_dim'] = channel_dim
            empty_metrics.append(metric_type(model, **metric_kwargs))
        return empty_metrics


    def _generate_default_kwargs_for_explainer(self, kwargs):
        return {
            'layer': kwargs.get('layer'),
            'background_data': kwargs.get('background_data'),
            'forward_arg_extractor': kwargs.get('forward_arg_extractor'),
            'additional_forward_arg_extractor': kwargs.get('additional_forward_arg_extractor'),
            'feature_mask_fn': kwargs.get('feature_mask_fn') \
                or get_default_feature_mask_fn(self.modality),
            'baseline_fn': kwargs.get('baseline_fn') \
                or get_default_baseline_fn(self.modality, mask_token_id=kwargs.get('mask_token_id') or 0),
        }

    def _generate_default_kwargs_for_metric(self, kwargs):
        return {
            'baseline_fn': kwargs.get('baseline_fn') \
                or get_default_baseline_fn(self.modality, mask_token_id=kwargs.get('mask_token_id')),
            'channel_dim': kwargs.get('channel_dim') \
                or get_default_channel_dim(self.modality)
        }

