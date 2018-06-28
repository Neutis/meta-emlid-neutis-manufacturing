DESCRIPTION = "Service & scripts to test Neutis N5 board"
LICENSE = "BSD"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/BSD;md5=3775480a712fc46a69647678acb234cb"

SRC_URI += "\
    file://self-tests.service \
    file://crypto_chip_test.c \
    file://self-tests.py \
    "

FILESEXTRAPATHS_prepend := "${THISDIR}/files/:"

SYSTEMD_SERVICE_${PN} = "self-tests.service"
SYSTEMD_AUTO_ENABLE = "enable"
SYSTEMD_AUTO_RESTART = "false"

RDEPENDS_${PN} = "systemd python python-serial openssl-atecc508a"
DEPENDS = "systemd python python-serial openssl-atecc508a"

inherit systemd

S = "${WORKDIR}"

INC_DIRS = "-I${STAGING_INCDIR}/ateccssl"
LIB_DIRS = "-L${STAGING_LIBDIR}"
LIBS = "-lateccssl"

do_compile() {
    ${CC} ${CFLAGS} ${LDFLAGS} ${LIB_DIRS} ${INC_DIRS} ${S}/crypto_chip_test.c -o crypto_chip_test ${LIBS}
}

do_install() {
    install -d ${D}${systemd_unitdir}/system
    install -m 0644 ${S}/self-tests.service ${D}${systemd_unitdir}/system

    install -d ${D}${base_sbindir}
    install -c -m 0755 ${B}/crypto_chip_test ${D}${base_sbindir}
    install -c -m 0755 ${S}/self-tests.py ${D}${base_sbindir}
}

systemd_postinst() {
OPTS=""

if [ -n "$D" ]; then
    OPTS="--root=$D"
fi

if type systemctl >/dev/null 2>/dev/null; then
    systemctl $OPTS ${SYSTEMD_AUTO_ENABLE} ${SYSTEMD_SERVICE}

    if [ -z "$D" -a "${SYSTEMD_AUTO_RESTART}" = "true" ]; then
        systemctl restart ${SYSTEMD_SERVICE}
    fi
fi
}

FILES_${PN} += "${base_libdir}/systemd/system/self-tests.service"
FILES_${PN} += "${base_sbindir}/crypto_chip_test"
FILES_${PN} += "${base_sbindir}/self-tests.py"
