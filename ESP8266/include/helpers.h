#ifndef HELPERS_H
#define HELPERS_H

#define CRISIS_CMD "CRISIS"

// This is the function for writing register. See "write_registers.S" for info.
extern "C" void write_register_asm(uint32_t a, uint32_t b);
#define write_register(reg, hostid, par, val) write_register_asm((hostid << 2) + 0x60000a00 + 0x300, (reg | (par << 8) | (val << 16) | 0x01000000))

// MAC addresses used.

const uint8_t nodes[2][6]
{
    {
        0xDE, 0x4F, 0x22, 0x18, 0x2F, 0xB0
    },
    {
        0x6A, 0xC6, 0x3A, 0xA5, 0x5F, 0x0E
    }
};

#endif
