# networkCommon/schema.py
"""
schema.py

Defines the expected structure, parameters, types, constraints, and defaults
for different components, especially detailed type-specific schemas for Layers.

Located in networkCommon as it defines structural contracts.
"""
import math
# Import only from networkCommon or standard libraries
from . import semantic_codes as codes # Relative import within networkCommon

# Maps component codes used in Error Correction context to schema keys
COMPONENT_CODE_TO_NAME = {
    '01': "Block",
    '02': "Layer", # Refers to BaseLayer schema, type-specific lookup needed
    '03': "Input",
    '04': "Output",
    '05': "MemoryBuffer",
    '06': "Predictor",
    '07': "Comparator",
    '08': "NoveltyModule",
    '09': "IntrinsicReward",
    '10': "PolicyHead",
    '11': "PlasticityRuleDef",
}

# --- Base Schemas ---
BASE_LAYER_SCHEMA = {
    # ... (content as defined previously, using codes.*) ...
    "layer_idx": {"type": int},
    "type": {"type": int},
    "params": {"type": dict, "default": {}},
    "skip_connections": {"type": list, "default": []},
    "activation": {"type": int, "default": codes.ACT_IDENTITY},
    "dropout": {"type": (float, type(None)), "default": None, "range": (0.0, 1.0)},
    "flags": {"type": set, "default": set()},
    "bias": {"type": bool, "default": True},
    "weight_init": {"type": (dict, type(None)), "default": None},
    "bias_init": {"type": (dict, type(None)), "default": None},
    "shape_constraints": {"type": (dict, type(None)), "default": None},
    "shape_references": {"type": (dict, type(None)), "default": None},
    "shape_adapter": {"type": (dict, type(None)), "default": None},
    "reshape": {"type": (dict, type(None)), "default": None},
    "shared_weights": {"type": (dict, type(None)), "default": None},
    "weight_scale": {"type": (float, type(None)), "default": None},
    "sparsity": {"type": (float, type(None)), "default": None, "range": (0.0, 1.0)},
    "plasticity_rules": {"type": (list, type(None)), "default": None},
    "plasticity_rate": {"type": (float, type(None)), "default": None},
    "conv_params": {"type": (dict, type(None)), "default": None},
    "lstm_params": {"type": (dict, type(None)), "default": None},
    "batchnorm_params": {"type": (dict, type(None)), "default": None},
    "maxpool_params": {"type": (dict, type(None)), "default": None},
    "attention": {"type": (dict, type(None)), "default": None},
    "dynamic_routing": {"type": (dict, type(None)), "default": None},
    "temporal_aggregation": {"type": (dict, type(None)), "default": None},
    "stateful": {"type": (dict, type(None)), "default": None},
    "recurrent_cell": {"type": (dict, type(None)), "default": None},
    "initial_state": {"type": (dict, type(None)), "default": None},
    "shape_checks": {"type": (dict, type(None)), "default": None},
    "raw_slices": {"type": (dict, type(None)), "default": None},
}

# --- Type-Specific Layer Schemas ---
LAYER_SPECIFIC_SCHEMAS = {
    codes.LAYER_LINEAR: {
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": True},
        "params": {
            codes.PARAM_OUT_FEATURES: {"type": int, "required": True},
            codes.PARAM_IN_FEATURES: {"type": int, "inferred": True},
        },
        "allowed_flags": {codes.FLAG_FREEZE, codes.FLAG_BIAS},
    },
    codes.LAYER_CONV1D: {
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": True},
        "params": {
            codes.PARAM_OUT_CHANNELS: {"type": int, "required": True},
            codes.PARAM_KERNEL_SIZE: {"type": (int, tuple), "required": True, "tuple_len": 1},
            codes.PARAM_STRIDE: {"type": (int, tuple), "default": 1, "tuple_len": 1},
            codes.PARAM_PADDING: {"type": (int, tuple, str), "default": 0, "tuple_len": 1},
            codes.PARAM_DILATION: {"type": (int, tuple), "default": 1, "tuple_len": 1},
            codes.PARAM_GROUPS: {"type": int, "default": 1},
            codes.PARAM_IN_CHANNELS: {"type": int, "inferred": True},
        },
         "allowed_flags": {codes.FLAG_FREEZE, codes.FLAG_BIAS},
    },
    # ... (all other LAYER_SPECIFIC_SCHEMAS as defined previously, using codes.*) ...
    codes.LAYER_CONV2D: { # Example
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": True},
        "params": {
            codes.PARAM_OUT_CHANNELS: {"type": int, "required": True},
            codes.PARAM_KERNEL_SIZE: {"type": (int, tuple), "required": True, "tuple_len": 2},
            codes.PARAM_STRIDE: {"type": (int, tuple), "default": (1,1), "tuple_len": 2},
            codes.PARAM_PADDING: {"type": (int, tuple, str), "default": 0, "tuple_len": 2},
            codes.PARAM_DILATION: {"type": (int, tuple), "default": (1,1), "tuple_len": 2},
            codes.PARAM_GROUPS: {"type": int, "default": 1},
            codes.PARAM_IN_CHANNELS: {"type": int, "inferred": True},
        },
         "allowed_flags": {codes.FLAG_FREEZE, codes.FLAG_BIAS},
    },
    codes.LAYER_CONV3D: { # Example
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": True},
        "params": {
            codes.PARAM_OUT_CHANNELS: {"type": int, "required": True},
            codes.PARAM_KERNEL_SIZE: {"type": (int, tuple), "required": True, "tuple_len": 3},
            codes.PARAM_STRIDE: {"type": (int, tuple), "default": (1,1,1), "tuple_len": 3},
            codes.PARAM_PADDING: {"type": (int, tuple, str), "default": 0, "tuple_len": 3},
            codes.PARAM_DILATION: {"type": (int, tuple), "default": (1,1,1), "tuple_len": 3},
            codes.PARAM_GROUPS: {"type": int, "default": 1},
            codes.PARAM_IN_CHANNELS: {"type": int, "inferred": True},
        },
         "allowed_flags": {codes.FLAG_FREEZE, codes.FLAG_BIAS},
    },
     codes.LAYER_LSTM: { # Example
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": True},
        "params": {
            codes.PARAM_HIDDEN_SIZE: {"type": int, "required": True},
            codes.PARAM_NUM_LAYERS: {"type": int, "default": 1},
            codes.PARAM_DROPOUT: {"type": float, "default": 0.0, "range": (0.0, 1.0)},
            codes.PARAM_INPUT_SIZE: {"type": int, "inferred": True},
        },
        "allowed_flags": {codes.FLAG_FREEZE, codes.FLAG_BIAS, codes.FLAG_BATCH_FIRST, codes.FLAG_BIDIRECTIONAL},
    },
    codes.LAYER_BATCHNORM1D: { # Example
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": None},
        "params": {
            codes.PARAM_NUM_FEATURES: {"type": int, "inferred": True},
            codes.PARAM_EPS: {"type": float, "default": 1e-5},
            codes.PARAM_MOMENTUM: {"type": (float, type(None)), "default": 0.1},
        },
        "allowed_flags": {codes.FLAG_AFFINE, codes.FLAG_TRACK_RUNNING_STATS},
    },
    codes.LAYER_GROUPNORM: { # Example
        "inherits": BASE_LAYER_SCHEMA,
        "bias": {"default": None},
         "params": {
            codes.PARAM_NUM_GROUPS: {"type": int, "required": True},
            codes.PARAM_NUM_FEATURES: {"type": int, "inferred": True},
            codes.PARAM_EPS: {"type": float, "default": 1e-5},
        },
        "allowed_flags": {codes.FLAG_AFFINE},
    },

}

# --- Schemas for Other Components ---
COMPONENT_SCHEMA = {
    "Block": {
        "type": {"type": int, "default": codes.BLOCK_SEQUENTIAL},
        "connections": {"type": list, "default": []},
        "attributes": {"type": dict, "default": {}},
        "flags": {"type": set, "default": set()},
        "subblocks": {"type": list, "default": []},
        "default_params": {"type": dict, "default": {}},
        "shape_info": {"type": (dict, type(None)), "default": None},
        "sequence_params": {"type": (dict, type(None)), "default": None},
    },
    "Layer": BASE_LAYER_SCHEMA,
    "Input": {
        "data_type": {"type": int, "default": 0},
        "shape": {"type": (list, tuple), "required": True},
        "attributes": {"type": dict, "default": {}},
        "connections": {"type": list, "default": []},
        "shape_derivation": {"type": (dict, type(None)), "default": None},
    },
    "Output": {
        "data_type": {"type": int, "default": 0},
        "shape": {"type": (list, tuple, type(None)), "default": None},
        "attributes": {"type": dict, "default": {}},
        "connections": {"type": list, "required": True},
        "shape_derivation": {"type": (dict, type(None)), "default": None},
    },
    "MemoryBuffer": {
         "size": {"type": int, "default": 100, "range": (1, math.inf)},
         "type": {"type": int, "default": codes.MEM_FIFO},
         "connections": {"type": list, "default": []},
         "params": {"type": dict, "default": {}}, # Type specific params
    },
    "Predictor": {
        "input": {"type": dict, "required": True},
        "target": {"type": dict, "required": True},
        "model_type": {"type": int, "default": codes.PRED_MODEL_LINEAR},
        "error_signals": {"type": list, "default": []},
        "params": {"type": dict, "default": {}},
    },
    "Comparator": {
        "source1": {"type": dict, "required": True},
        "source2": {"type": dict, "required": True},
        "metric": {"type": int, "default": codes.METRIC_MSE},
        "connections": {"type": list, "default": []},
    },
    "NoveltyModule": {
        "input": {"type": dict, "required": True},
        "memory_buffer_id": {"type": int, "default": -1},
        "method": {"type": int, "default": codes.NOVELTY_PRED_ERROR_BASED},
        "params": {"type": dict, "default": {}},
    },
    "IntrinsicReward": {
        "source_type": {"type": int, "required": True},
        "source_id": {"type": int, "required": True},
        "scaling_int": {"type": int, "default": 100},
    },
    "PolicyHead": {
        "action_space": {"type": dict, "required": True},
        "params_int": {"type": dict, "default": {}},
        "connections": {"type": list, "default": []},
    },
    "PlasticityRuleDef": { # Definition stored in net.meta['plasticity_rules']
        "type": {"type": int, "required": True},
        "params_int": {"type": dict, "default": {}},
        "rate_int": {"type": (int, type(None)), "default": None},
    },
}