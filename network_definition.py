#!/usr/bin/env python3
"""
network_definition.py (in networkCommon)

Defines the shared network object classes used by interpreter and compiler.
"""

from typing import Dict, List, Any, Set, Tuple, Optional

# Import LoggingManager from its future location in networkCommon
# If LoggingManager hasn't been moved yet, this will cause a temporary error,
# but it will be correct after the next step.
# from .logging_manager import LoggingManager
# logger = LoggingManager.get_logger("NetworkDefinition")
# Temporarily disable logger usage until LoggingManager is moved and import confirmed
import logging
logger = logging.getLogger("NetworkDefinition_Common") # Placeholder logger

class NetworkDefinitionObj:
    """Final, structured representation of the interpreted network."""
    def __init__(self):
        self.blocks: Dict[int, BlockDefinition] = {}
        self.layers: Dict[int, List[LayerDefinition]] = {}
        self.inputs: Dict[int, InputDefinition] = {}
        self.outputs: Dict[int, OutputDefinition] = {}
        self.memories: Dict[str, Any] = {}
        self.meta_info: Dict[str, Any] = {}
        self.plasticity_rules: Dict[int, Dict] = {}
        self.plasticity_modulations: List[Dict] = []
        self.memory_buffers: Dict[int, Dict] = {}
        self.predictors: Dict[int, Dict] = {}
        self.comparators: Dict[int, Dict] = {}
        self.novelty_modules: Dict[int, Dict] = {}
        self.intrinsic_rewards: Dict[int, Dict] = {}
        self.signal_routes: List[Dict] = []
        self.policy_heads: Dict[int, Dict] = {}
        self.recurrent_connections: List[Dict] = []
        self.layer_shape_conditionals: List[Dict] = []

    def __repr__(self):
        parts = ["NetworkDefinitionObj:"]
        parts.append("  Meta Info: " + repr(self.meta_info))
        if self.memories:
            parts.append("  Memories: " + repr(self.memories))
        if self.plasticity_rules:
            parts.append("  Plasticity Rules: " + repr(self.plasticity_rules))
        if self.blocks:
            parts.append("  Blocks:")
            for bid, blk in sorted(self.blocks.items()):
                parts.append("    " + repr(blk))
        if self.layers:
            parts.append("  Layers:")
            for bid, layers in sorted(self.layers.items()):
                parts.append(f"    Block {bid}:")
                for layer in sorted(layers, key=lambda x: x.layer_idx):
                    parts.append("      " + repr(layer))
        if self.inputs:
            parts.append("  Inputs:")
            for iid, inp in sorted(self.inputs.items()):
                parts.append("    " + repr(inp))
        if self.outputs:
            parts.append("  Outputs:")
            for oid, outp in sorted(self.outputs.items()):
                parts.append("    " + repr(outp))
        # Add repr for other fields if needed
        return "\n".join(parts)


class BlockDefinition:
    """Represents a block in the final network definition."""
    def __init__(self, block_id: int, block_type: Any, connections: List[int],
                 attributes: Dict[str, Any], flags: Set[str], subblocks: List[int],
                 default_params: Dict[str, Any],
                 shape_info: Optional[Dict] = None, **kwargs):
        self.block_id = block_id
        self.block_type = block_type
        self.connections = connections
        self.attributes = attributes
        self.flags = flags
        self.subblocks = subblocks
        self.default_params = default_params
        self.shape_info = shape_info
        self.extra_properties = kwargs # Store any unexpected args from conversion

    def __repr__(self):
        extra = f", extra={self.extra_properties}" if self.extra_properties else ""
        shape = f", shape={self.shape_info}" if self.shape_info else ""
        defaults = f", defaults={self.default_params}" if self.default_params else ""
        return (f"Block(id={self.block_id}, type={self.block_type}, conns={self.connections}, "
                f"attrs={self.attributes}, flags={self.flags}, subs={self.subblocks}"
                f"{defaults}{shape}{extra})")


class LayerDefinition:
    """Represents a layer in the final network definition."""
    def __init__(self, block_id: int, layer_idx: int, layer_type: Any, params: Dict[str, Any],
                 skip_connections: List[int], activation: Any, dropout: Optional[float],
                 flags: Set[str], bias: bool,
                 raw_weights: Optional[List[str]] = None,
                 raw_biases: Optional[List[str]] = None,
                 weight_init: Optional[Dict] = None,
                 bias_init: Optional[Dict] = None,
                 shape_constraints: Optional[Dict] = None,
                 shape_references: Optional[Dict] = None,
                 shape_adapter: Optional[Dict] = None,
                 reshape: Optional[Dict] = None,
                 shared_weights: Optional[Dict] = None,
                 weight_scale: Optional[float] = None, # Changed from int based on description
                 sparsity: Optional[float] = None, # Assuming float
                 plasticity_rules: Optional[List[Dict]] = None,
                 plasticity_rate: Optional[float] = None, # Assuming float, though likely unused
                 # Add fields from description if missing (e.g., recurrent_cell, initial_state)
                 recurrent_cell: Optional[Dict] = None,
                 initial_state: Optional[Dict] = None,
                 temporal_aggregation: Optional[Dict] = None,
                 **kwargs):
        self.block_id = block_id
        self.layer_idx = layer_idx
        self.layer_type = layer_type
        self.params = params
        self.skip_connections = skip_connections
        self.activation = activation
        self.dropout = dropout
        self.flags = flags
        self.bias = bias
        self.raw_weights = raw_weights
        self.raw_biases = raw_biases
        self.weight_init = weight_init
        self.bias_init = bias_init
        self.shape_constraints = shape_constraints
        self.shape_references = shape_references
        self.shape_adapter = shape_adapter
        self.reshape = reshape
        self.shared_weights = shared_weights
        self.weight_scale = weight_scale
        self.sparsity = sparsity
        self.plasticity_rules = plasticity_rules
        self.plasticity_rate = plasticity_rate
        self.recurrent_cell = recurrent_cell
        self.initial_state = initial_state
        self.temporal_aggregation = temporal_aggregation
        self.extra_properties = kwargs # Store any unexpected args from conversion

    def __repr__(self):
        extra = f", extra={self.extra_properties}" if self.extra_properties else ""
        init = f", W_init={self.weight_init}, B_init={self.bias_init}" if (self.weight_init or self.bias_init) else ""
        shape = f", shape_constr={self.shape_constraints}, shape_ref={self.shape_references}" if (self.shape_constraints or self.shape_references) else ""
        raw = f", raw_W={len(self.raw_weights) if self.raw_weights else 0}, raw_B={len(self.raw_biases) if self.raw_biases else 0}" if (self.raw_weights or self.raw_biases) else ""
        plast = f", plasticity={self.plasticity_rules}" if self.plasticity_rules else ""
        return (f"Layer(idx={self.layer_idx}, type={self.layer_type}, params={self.params}, "
                f"skip={self.skip_connections}, act={self.activation}, dropout={self.dropout}, "
                f"flags={self.flags}, bias={self.bias}{init}{shape}{raw}{plast}{extra})")


class InputDefinition:
    """Represents an input node in the final network definition."""
    def __init__(self, input_id: int, data_type: Any, shape: Any,
                 attributes: Dict[str, Any], connections: List[Tuple[int, int]],
                 shape_derivation: Optional[Dict] = None):
        self.input_id = input_id
        self.data_type = data_type
        self.shape = shape
        self.attributes = attributes
        self.connections = connections
        self.shape_derivation = shape_derivation

    def __repr__(self):
        deriv = f", shape_deriv={self.shape_derivation}" if self.shape_derivation else ""
        return (f"Input(id={self.input_id}, data_type={self.data_type}, shape={self.shape}, "
                f"attrs={self.attributes}, conns={self.connections}{deriv})")


class OutputDefinition:
    """Represents an output node in the final network definition."""
    def __init__(self, output_id: int, data_type: Any, shape: Any,
                 attributes: Dict[str, Any], connections: List[Dict[str, int]],
                 shape_derivation: Optional[Dict] = None):
        self.output_id = output_id
        self.data_type = data_type
        self.shape = shape
        self.attributes = attributes
        self.connections = connections
        self.shape_derivation = shape_derivation

    def __repr__(self):
        deriv = f", shape_deriv={self.shape_derivation}" if self.shape_derivation else ""
        return (f"Output(id={self.output_id}, data_type={self.data_type}, shape={self.shape}, "
                f"attrs={self.attributes}, conns={self.connections}{deriv})")