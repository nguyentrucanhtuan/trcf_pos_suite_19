/** @odoo-module **/

import { session } from "@web/session";

function applyCompanyLogo(targetEl) {
    const companyId = session.company_id;
    if (!companyId || !targetEl) {
        return;
    }
    const logoUrl = `/web/image/res.company/${companyId}/logo`;
    if (targetEl.tagName === "IMG") {
        targetEl.setAttribute("src", logoUrl);
    }
    targetEl.style.setProperty("--navbar-logo", `url('${logoUrl}')`);
}

function initPosNavbarLogo() {
    const existing = document.querySelector(".pos-logo");
    if (existing) {
        applyCompanyLogo(existing);
        return;
    }

    const observer = new MutationObserver((_mutations, obs) => {
        const el = document.querySelector(".pos-logo");
        if (el) {
            applyCompanyLogo(el);
            obs.disconnect();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(() => {
        observer.disconnect();
    }, 10000);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPosNavbarLogo);
} else {
    initPosNavbarLogo();
}
