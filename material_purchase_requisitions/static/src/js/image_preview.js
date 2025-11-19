/** @odoo-module **/

import { registry } from "@web/core/registry";
import { onMounted } from "@odoo/owl";

const imagePreview = {
    mounted() {
        document.addEventListener('click', function(e) {
            if (e.target.closest('.clickable_preview')) {
                const tr = e.target.closest('tr');
                const id = tr.dataset.id;

                if (id) {
                    tr.closest('.o_list_view')
                      .component.env.services.action.doAction({
                          type: 'ir.actions.act_window',
                          name: 'Image Preview',
                          res_model: tr.dataset.model,
                          res_id: parseInt(id),
                          view_mode: 'form',
                          target: 'new',
                      });
                }
            }
        });
    },
};

registry.category("main_components").add("imagePreview", imagePreview);
