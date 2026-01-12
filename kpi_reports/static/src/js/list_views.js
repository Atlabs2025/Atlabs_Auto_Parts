/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();

        onMounted(() => {
            setTimeout(() => {
                if (!this.el) {
                    return;
                }

                // 🔒 KPI report only
                if (this.props.list?.resModel !== "kpi.parts.report") {
                    return;
                }

                /* ---------- HEADER ---------- */
                const th = this.el.querySelector('th[data-name="sn"]');
                if (th) {
                    th.classList.remove("o_list_number"); // 🔥 KEY FIX
                    th.style.textAlign = "left";
                    th.style.paddingLeft = "2px";
                }

                /* ---------- BODY ---------- */
                this.el.querySelectorAll('td[data-name="sn"]').forEach(td => {
                    td.classList.remove("o_list_number"); // 🔥 KEY FIX
                    td.style.textAlign = "left";
                    td.style.paddingLeft = "2px";
                });

            }, 0);
        });
    },
});
