/*Written by Aleksandr Aleksandrov <aleksandr.aleksandrov@emlid.com>
*
* Copyright (c) 2018, Emlid Limited
* All rights reserved.
*
* Redistribution and use in source and binary forms,
* with or without modification,
* are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice,
* this list of conditions and the following disclaimer.
*
* 2. Redistributions in binary form must reproduce the above copyright notice,
* this list of conditions and the following disclaimer in the documentation
* and/or other materials provided with the distribution.
*
* 3. Neither the name of the copyright holder nor the names of its contributors
* may be used to endorse or promote products derived from this software
* without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
* THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
* FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
* IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
* BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
* OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
* PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
* DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
* AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
* STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
* ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
* EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.*/

#include <stdio.h>
#include <unistd.h>
#include <cryptoauthlib.h>

#define PRIVATE_KEY_SLOT    0

#define I2C_SLAVE_ADDRESS   0xC0
#define I2C_BUS             0
#define I2C_BAUD            100000

#define IFACE_WAKE_DELAY    1500
#define IFACE_RX_RETRIES    20

static ATCAIfaceCfg g_iface_config = {
    .iface_type = ATCA_I2C_IFACE,
    .devtype = ATECC508A,
    .atcai2c = {
        .slave_address = I2C_SLAVE_ADDRESS,
        .bus = I2C_BUS,
        .baud = I2C_BAUD,
    },
    .wake_delay = IFACE_WAKE_DELAY,
    .rx_retries = IFACE_RX_RETRIES};

static void print_byte_in_hex(const uint8_t *bytes, size_t size)
{
    for (int i = 0; i < size; i++)
    {
        printf("%02X", bytes[i]);
    }
}

static ATCA_STATUS provision_keys()
{
    ATCA_STATUS status = ATCA_EXECUTION_ERROR;
    uint8_t public_key[ATCA_PUB_KEY_SIZE];

    do
    {
        atcab_lock_config_zone();

        if ((status = atcab_get_pubkey(PRIVATE_KEY_SLOT, &public_key)) == ATCA_SUCCESS)
            break;

        if ((status = atcab_genkey(PRIVATE_KEY_SLOT, &public_key)) != ATCA_SUCCESS)
            break;

    } while (0);

    if (status == ATCA_SUCCESS)
        print_byte_in_hex(&public_key, sizeof(public_key));

    return status;
}

int main(int argc, char *argv[])
{
    int opt;
    ATCA_STATUS provisioning_status = ATCA_EXECUTION_ERROR;

    ATCA_STATUS atca_init_status = atcab_init(&g_iface_config);

    if (atca_init_status != ATCA_SUCCESS)
        return 1;

    while ((opt = getopt(argc, argv, "p")) != -1)
    {
        switch (opt)
        {
        case 'p':
            provisioning_status = provision_keys();
            break;
        default:
            break;
        }
    }

    atcab_release();

    if (provisioning_status != ATCA_SUCCESS)
        return 1;

    return 0;
}
