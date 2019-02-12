.globl write_register_asm
.type write_register_asm, @function
.align 4
write_register_asm:
	_s32i.n	a3, a2, 0
	_memw
	_l32i.n	a3, a2, 0
	bbci	a3, 25, .term_write_register
.reloop_write_register:
	_memw
	_l32i.n	a3, a2, 0
	bbsi	a3, 25, .reloop_write_register
.term_write_register:
	_ret.n
