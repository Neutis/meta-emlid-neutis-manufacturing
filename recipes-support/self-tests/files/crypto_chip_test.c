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
