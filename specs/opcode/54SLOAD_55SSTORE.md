# SLOAD & SSTORE opcodes

## Variables definition

| Name | Value |
| - | - |
| COLD_SLOAD_COST | 2100 |
| WARM_STORAGE_READ_COST | 100 |
| SLOAD_GAS | 100 |
| SSTORE_SET_GAS | 20000 |
| SSTORE_RESET_GAS | 2900 |
| SSTORE_CLEARS_SCHEDULE | 4800 |

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x54) for `SLOAD`
   2. opId === OpcodeId(0x55) for `SSTORE`
2. state transition:
   - gc
     - `SLOAD`: +8
       - 4 call_context read
       - 2 stack operations
       - 1 storage reads
       - 1 access_list write
     - `SSTORE`: +10
       - 5 call_context read
       - 2 stack operations
       - 1 storage reads/writes
       - 1 access_list write
       - 1 gas_refund writes
   - stack_pointer
     - `SLOAD`: remains the same
     - `SSTORE`: -2
   - pc + 1
   - reversible_write_counter
     - `SLOAD`: +1 (access_list)
     - `SSTORE`: +3 (for storage, access_list & gas_refund respectively)
   - gas:
     - `SLOAD`:
       - the accessed `key` is warm: gas + WARM_STORAGE_READ_COST
       - the accessed `key` is cold: gas + COLD_SLOAD_COST
     - `SSTORE`:
       - the accessed `key` is warm:
         - `current_value == new_value`: gas + SLOAD_GAS
         - `current_value != new_value`:
           - `original_value == current_value`:
             - `original_value == 0`: gas + SSTORE_SET_GAS
             - `original_value != 0`: gas + SSTORE_RESET_GAS
           - `original_value != current_value`: gas + SLOAD_GAS
       - the accessed `key` is cold:
         - `current_value == new_value`: gas + SLOAD_GAS + COLD_SLOAD_COST
         - `current_value != new_value`:
           - `original_value == current_value`:
             - `original_value == 0`: gas + SSTORE_SET_GAS + COLD_SLOAD_COST
             - `original_value != 0`: gas + SSTORE_RESET_GAS + COLD_SLOAD_COST
           - `original_value != current_value`: gas + SLOAD_GAS + COLD_SLOAD_COST
   * gas_refund:
     - `SSTORE`:
       - `current_value != new_value`:
         - `original_value == current_value`:
           - `original_value != 0` && `new_value == 0`: gas_refund + SSTORE_CLEARS_SCHEDULE
         - `original_value != current_value`:
           - `original_value != 0`:
             - `current_value == 0`: gas_refund - SSTORE_CLEARS_SCHEDULE
             - `new_value == 0`: gas_refund + SSTORE_CLEARS_SCHEDULE
           - `original_value == new_value`:
             - `original_value == 0`: gas_refund + SSTORE_SET_GAS - SLOAD_GAS
             - `original_value != 0`: gas_refund + SSTORE_RESET_GAS - SLOAD_GAS
3. lookups:
   - `SLOAD`: 8 busmapping lookups
     - call_context:
       - `tx_id`: Read the `tx_id` for this tx.
       - `rw_counter_end_of_reversion`: Read the `rw_counter_end` if this tx get reverted.
       - `is_persistent`: Read if this tx will be reverted.
       - `callee_address`: Read the `callee_address` of this call.
     - stack:
       - `key` is popped off the top of the stack
       - `value` is pushed on top of the stack
     - storage: The 32 bytes of `value` are read from storage at `key`
     - access_list: Write as `true` for `key`
   - `SSTORE`: 10 busmapping lookups
     - call_context:
       - `tx_id`: Read the `tx_id` for this tx.
       - `is_static`: Read the call's property `is_static`
       - `rw_counter_end_of_reversion`: Read the `rw_counter_end` if this tx get reverted.
       - `is_persistent`: Read if this tx will be reverted.
       - `callee_address`: Read the `callee_address` of this call.
     - stack:
       - `key` is popped off the top of the stack
       - `value` is popped off the top of the stack
     - storage:
       - The 32 bytes of new `value` are written to storage at `key`, with the previous `value` and `committed_value`
     - access_list: Write as `true` for `key`
     - gas_refund:
       - Write the new accumulated gas_refund for this tx

## Exceptions

1. gas out: remaining gas is not enough
2. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `SSTORE`: contains a single value: `1023 == stack_pointer`
3. context error
   - only for `SSTORE`: the current execution context is from a `STATICCALL` (since Byzantium fork).
