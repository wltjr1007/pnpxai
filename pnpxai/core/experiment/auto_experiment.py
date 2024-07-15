from typing import Literal, Callable, Optional

from pnpxai.core.experiment.experiment import Experiment
from pnpxai.core.detector import detect_model_architecture
from pnpxai.core.recommender import XaiRecommender
# from pnpxai.core.recommender.recommender import XaiRecommender, RecommenderOutput
from pnpxai.core._types import DataSource, Model, ModalityOrListOfModalities, Question, Modality
# from pnpxai.core.experiment.utils import init_explainers, init_metrics
from pnpxai.explainers import CAM_BASED_EXPLAINERS, ATTENTION_SPECIFIC_EXPLAINERS, PERTURBATION_BASED_EXPLAINERS
from pnpxai.explainers.types import TargetLayerOrListOfTargetLayers, ForwardArgumentExtractor


class AutoExperiment(Experiment):
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
        question: Question = "why",
        evaluator_enabled: bool = True,
        layer: Optional[TargetLayerOrListOfTargetLayers] = None,
        input_extractor: Optional[Callable] = None,
        label_extractor: Optional[Callable] = None,
        target_extractor: Optional[Callable] = None,
        forward_arg_extractor: Optional[ForwardArgumentExtractor] = None,
        additional_forward_arg_extractor: Optional[ForwardArgumentExtractor] = None,
        input_visualizer: Optional[Callable] = None,
        target_visualizer: Optional[Callable] = None,
        target_labels: bool = False,
    ):
        # TODO: multimodal support
        if modality not in Modality.__args__:
            raise NotImplementedError(f'AutoExperiment for {modality} is not supported.')

        if (modality == 'text' or 'text' in modality):
            assert layer is not None, "Must have 'layer' for text modality. It might be a word embedding layer of your model."

        # recommender
        self.recommended = XaiRecommender().recommend(modality=modality, model=model)

        # explainers
        explainer_kwargs = {
            'forward_arg_extractor': forward_arg_extractor,
            'additional_forward_arg_extractor': additional_forward_arg_extractor,
        }
        if layer is not None:
            explainer_kwargs['layer'] = layer

        explainers = []
        for explainer_type in self.recommended.explainers:
            if explainer_type in CAM_BASED_EXPLAINERS:
                explainer = explainer_type(model)
            elif explainer_type in ATTENTION_SPECIFIC_EXPLAINERS + PERTURBATION_BASED_EXPLAINERS:
                explainer = explainer_type(
                    model,
                    forward_arg_extractor=forward_arg_extractor,
                    additional_forward_arg_extractor=additional_forward_arg_extractor,
                )
            else:
                explainer = explainer_type(
                    model,
                    layer=layer,
                    forward_arg_extractor=forward_arg_extractor,
                    additional_forward_arg_extractor=additional_forward_arg_extractor,
                )
            explainers.append(explainer)
        metrics = [
            metric_type(model, explainer)
            for metric_type in self.recommended.metrics
        ]
        super().__init__(
            model=model,
            data=data,
            explainers=explainers,
            metrics=metrics,
            modality=modality,
            input_extractor=input_extractor,
            label_extractor=label_extractor,
            target_extractor=target_extractor,
            input_visualizer=input_visualizer,
            target_visualizer=target_visualizer,
            target_labels=target_labels,
        )

    
    # @staticmethod
    # def recommend(model: Model, question: Question, task: Task) -> RecommenderOutput:
    #     """
    #     Recommend explainers and metrics based on the model architecture.

    #     Parameters:
    #         model (1Model): The machine learning model to recommend explainers for.
    #         question (Question): The type of question the experiment aims to answer.
    #         task (Task): The type of task the model is designed for.

    #     Returns:
    #         RecommenderOutput: Output containing recommended explainers and metrics.
    #     """
    #     model_arch = detect_model_architecture(model)

    #     recommender = XaiRecommender()
    #     recommender_out = recommender(question, task, model_arch)

    #     return recommender_out
