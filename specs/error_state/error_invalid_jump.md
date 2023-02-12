# ErrorOutOfGasConstant state

## Procedure
this type of error only occurs when executing op code is `JUMP` or `JUMPI`.

### EVM behavior

Pop one EVM word `dest` from the stack, then go to `ErrorInvalidJump` state when 
one of the followings occurs:

-  `dest` is not within code length range
-  `dest` is a not `JUMPDEST` code , or data section of PUSH*

### Constraints
1. `dest` is out of range or not`JUMPDEST` code
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- Byte code lookup.
- Call Context lookup `CallContextFieldTag.IsSuccess`

## Code

Please refer to `src/zkevm_specs/evm/execution/error_Invalid_jump.py`.
