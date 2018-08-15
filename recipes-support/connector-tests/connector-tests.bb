DESCRIPTION = "Service & scripts to test Neutis N5 board's connectors"
LICENSE = "BSD"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/BSD;md5=3775480a712fc46a69647678acb234cb"

SRC_URI += "\
    file://connector-tests.service \
    file://connector-tests.py \
    "

FILESEXTRAPATHS_prepend := "${THISDIR}/files/:"

SYSTEMD_SERVICE_${PN} = "connector-tests.service"
SYSTEMD_AUTO_ENABLE = "enable"
SYSTEMD_AUTO_RESTART = "false"

RDEPENDS_${PN} = "systemd python python3-systemd"
DEPENDS = "systemd python python3-systemd"

inherit systemd

S = "${WORKDIR}"

do_install() {
    install -d ${D}${systemd_unitdir}/system
    install -m 0644 ${S}/connector-tests.service ${D}${systemd_unitdir}/system

    install -d ${D}${base_sbindir}
    install -c -m 0755 ${S}/connector-tests.py ${D}${base_sbindir}
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

FILES_${PN} += "${base_libdir}/systemd/system/connector-tests.service"
FILES_${PN} += "${base_sbindir}/connector-tests.py"
