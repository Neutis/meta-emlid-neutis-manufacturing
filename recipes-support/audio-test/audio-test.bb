DESCRIPTION = "Script for testing Neutis N5 audio"
LICENSE = "BSD"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/BSD;md5=3775480a712fc46a69647678acb234cb"

SRC_URI += "file://audio-test.py"

FILESEXTRAPATHS_prepend := "${THISDIR}/files/:"

RDEPENDS_${PN} = "python python3-pyalsaaudio"
DEPENDS = "python python3-pyalsaaudio"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${base_sbindir}
    install -c -m 0755 ${S}/audio-test.py ${D}${base_sbindir}
}

