from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, RW, CopyDataTypeTag
from zkevm_specs.util import N_BYTES_MEMORY_SIZE


def returndatacopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    memory_offset_word, offset_word, size_word = (
        instruction.stack_pop(),
        instruction.stack_pop(),
        instruction.stack_pop(),
    )

    last_callee_id = instruction.call_context_lookup(CallContextFieldTag.LastCalleeId)
    return_data_length = instruction.call_context_lookup(
        CallContextFieldTag.LastCalleeReturnDataLength, RW.Read
    )
    return_data_offset = instruction.call_context_lookup(
        CallContextFieldTag.LastCalleeReturnDataOffset, RW.Read
    )

    # out-of-bound-check
    instruction.range_check(
        return_data_length.expr()
        - (
            instruction.rlc_to_fq(offset_word, 8).expr()
            + instruction.rlc_to_fq(size_word, 8).expr()
        ),
        N_BYTES_MEMORY_SIZE,
    )

    memory_offset, size = instruction.memory_offset_and_length(memory_offset_word, size_word)
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, size
    )
    gas_cost = instruction.memory_copier_gas_cost(size, memory_expansion_gas_cost)

    copy_rwc_inc, _ = instruction.copy_lookup(
        last_callee_id,
        CopyDataTypeTag.Memory,
        instruction.curr.call_id,
        CopyDataTypeTag.Memory,
        return_data_offset,
        return_data_offset + size,
        memory_offset,
        size,
        instruction.curr.rw_counter + instruction.rw_counter_offset,
    )

    assert copy_rwc_inc == size * 2
    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + copy_rwc_inc),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(3),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
